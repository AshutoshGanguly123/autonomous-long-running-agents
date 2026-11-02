from __future__ import annotations

import hashlib
import json
import urllib.request
from .store import dumps


class ContextLimit(ValueError):
    pass


class Model:
    def __init__(self, store, config, tokenizer=None):
        self.store, self.config = store, config
        if tokenizer is None:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(config['tokenizer'], local_files_only=True)
        self.tokenizer = tokenizer
        self.limit = config.get('context_tokens', 32768)
        if not 1024 <= self.limit <= 32768:
            raise ValueError('Context ceiling must not exceed 32768')
        self.output = config.get('generation_reserve_tokens', config.get('max_output_tokens',8192))

    def count(self, messages):
        return len(self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                   enable_thinking=self.config.get('thinking', True)))

    def text_tokens(self, text):
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def clip(self, text, tokens):
        ids = self.tokenizer.encode(text, add_special_tokens=False)
        if len(ids) <= tokens:
            return text
        return self.tokenizer.decode(ids[:max(0,tokens)], skip_special_tokens=True) + '\n[View shortened; full artifact remains readable by reference.]'

    def call(self, key, node, messages, max_tokens=None):
        body = {'model': self.config['model'], 'messages': messages,
                'temperature': self.config.get('temperature', .6),
                'chat_template_kwargs': {'enable_thinking': self.config.get('thinking', True)}}
        # Ordinary scientist/worker calls may use the whole remaining window.
        # `output` is a packing/rollover reserve, not another generation quota.
        body['max_tokens'] = min(max_tokens or self.limit, self.limit - self.count(messages))
        prompt_tokens = self.count(messages)
        if body['max_tokens'] < 1 or prompt_tokens + body['max_tokens'] > self.limit:
            raise ContextLimit('Complete rendered request exceeds context ceiling')
        cache_key = 'model:' + key
        fingerprint = hashlib.sha256(dumps(body).encode()).hexdigest()
        cached = self.store.get(cache_key)
        if cached:
            if cached['fingerprint'] != fingerprint:
                raise RuntimeError('Resume request differs from the recorded request; use a new campaign')
            return cached['response']
        request_ref = self.store.artifact('request:' + key, node, 'model_request', dumps(body))
        self.store.put('pending:' + key, {'fingerprint': fingerprint, 'request_ref': request_ref,
                                        'prompt_tokens': prompt_tokens, 'max_tokens': body['max_tokens']})
        req = urllib.request.Request(self.config['base_url'].rstrip('/')+'/chat/completions',
                                     data=dumps(body).encode(), headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=self.config.get('timeout_seconds', 1800)) as response:
                result = json.load(response)
        except Exception as exc:
            self.store.artifact('error:' + key, node, 'model_error', repr(exc))
            raise
        self.store.artifact('response:' + key, node, 'model_response', dumps(result))
        usage = result.get('usage', {})
        if usage.get('prompt_tokens', prompt_tokens) != prompt_tokens:
            raise RuntimeError(f"Tokenizer/server prompt count mismatch: {prompt_tokens} versus {usage.get('prompt_tokens')}")
        if usage.get('total_tokens', prompt_tokens) > self.limit:
            raise ContextLimit('Server reported total tokens above the context ceiling')
        choice = result['choices'][0]
        answer = {'text': choice['message'].get('content') or '', 'usage': usage,
                  'finish_reason': choice.get('finish_reason'), 'request_ref': request_ref}
        self.store.put(cache_key, {'fingerprint': fingerprint, 'response': answer})
        return answer
