#!/usr/bin/env bash
set -euo pipefail
cd ${REPO_ROOT}
base_python=<local-home>/agent_memory/amemgym_hierarchy/serve-venv/bin/python
"$base_python" -m venv --without-pip .venv
<local-home>/.local/bin/uv pip install --python .venv/bin/python pip
base_site=$("$base_python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
task_site=$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
printf '%s\n' "$base_site" > "$task_site/existing-serving-runtime.pth"
.venv/bin/pip install rdkit 'sentence-transformers==5.1.2' 'transformers==4.57.6' 'tokenizers==0.22.2' 'huggingface-hub==0.36.2' pytest
.venv/bin/pip install --no-deps guacamol
.venv/bin/python - <<'PY'
from pathlib import Path
import json, os
from huggingface_hub import snapshot_download, model_info
project=Path.cwd()
name='sentence-transformers/all-mpnet-base-v2'
revision=model_info(name).sha
snapshot=snapshot_download(name,revision=revision,
    cache_dir='${REPO_ROOT}/models/hf',
    ignore_patterns=['onnx/*','openvino/*','*.h5','*.msgpack','rust_model.ot','pytorch_model.bin'])
config=json.loads((project/'config.hpc.json').read_text())
config['embedding_model']=snapshot
config['embedding_revision']=revision
config['generation_reserve_tokens']=config.pop('max_output_tokens',config.get('generation_reserve_tokens',8192))
(project/'config.hpc.json').write_text(json.dumps(config,indent=2)+'\n')
probe=project/'ops/storage-probe.bin'
payload=os.urandom(1024*1024)
with probe.open('wb') as f:
    f.write(payload); f.flush(); os.fsync(f.fileno())
assert probe.read_bytes()==payload
probe.unlink()
print(json.dumps({'setup':'ready','embedding_model':snapshot,'storage_fsync':'passed'}))
PY
.venv/bin/python -m pip freeze > ops/runtime-packages.txt
