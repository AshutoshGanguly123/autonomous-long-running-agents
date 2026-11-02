"""Launch the existing frozen model on explicitly empty, unreserved cards."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--config',required=True)
p.add_argument('--gpu-indices',required=True)
p.add_argument('--record',required=True)
args = p.parse_args()
config = json.loads(Path(args.config).read_text())
host = socket.gethostname().split('.')[0]
if not re.fullmatch(r'gpu-\d+',host):
    raise RuntimeError('Use a compute node')
indices = [int(x) for x in args.gpu_indices.split(',')]
if len(indices)!=2 or len(set(indices))!=2:
    raise RuntimeError('This deployment needs two distinct cards')
scheduler = subprocess.check_output(['scontrol','--details','--oneliner','show','node',host],text=True)
state = re.search(r'\bState=(\S+)',scheduler).group(1)
if state.split('+')[0] not in {'IDLE','MIXED'} or any(x in state for x in ['DRAIN','DOWN','FAIL','RESERVED','PLANNED']):
    raise RuntimeError('Unavailable or ambiguously reserved node: '+state)
used = re.search(r'\bGresUsed=(\S+)',scheduler)
if used is None:
    raise RuntimeError('Missing reservation details')
reserved = set()
for value in re.findall(r'IDX:([0-9,\-]+)',used.group(1)):
    for term in value.split(','):
        if '-' in term:
            first,last=map(int,term.split('-')); reserved.update(range(first,last+1))
        else:
            reserved.add(int(term))
if not reserved and re.search(r':([1-9][0-9]*)\b',used.group(1)):
    raise RuntimeError('Ambiguous GPU reservations')
lines = subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,pci.bus_id,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
cards = {}
for line in lines.splitlines():
    index,uuid,pci,memory,util=[s.strip() for s in line.split(',')]
    cards[int(index)]={'uuid':uuid,'pci':pci,'memory':int(memory),'utilization':int(util)}
if [i for i,_ in sorted(cards.items(),key=lambda item:item[1]['pci'])] != sorted(cards):
    raise RuntimeError('NVML and PCI ordering disagree')
processes = subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
for i in indices:
    c=cards[i]
    if i in reserved or c['memory']>20 or c['utilization'] or c['uuid'] in processes:
        raise RuntimeError(f'Card {i} is not physically empty and unreserved')
port = int(config['base_url'].split(':')[-1].split('/')[0])
with socket.socket() as sock:
    sock.bind(('127.0.0.1',port))
base=Path('<local-home>/agent_memory/amemgym_hierarchy')
command=[str(base/'serve-venv/bin/vllm'),'serve',config['tokenizer'],
         '--served-model-name',config['model'],'--host','127.0.0.1','--port',str(port),
         '--dtype','bfloat16','--tensor-parallel-size','2','--max-model-len','32768',
         '--max-num-seqs','2','--gpu-memory-utilization','0.85']
if config.get('enforce_eager', True):
    command.append('--enforce-eager')
command += ['--disable-custom-all-reduce','--reasoning-parser','qwen3']
record={'node':host,'pid':os.getpid(),'time':time.time(),'cards':{i:cards[i] for i in indices},
        'scheduler':scheduler,'command':command,'config':config}
Path(args.record).write_text(json.dumps(record,indent=2))
cache=Path(args.record).parent/'runtime-cache'
cache.mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES=','.join(map(str,indices)),CUDA_DEVICE_ORDER='PCI_BUS_ID',
                  HF_HUB_OFFLINE='1',NCCL_P2P_DISABLE='1',NCCL_IB_DISABLE='1',
                  VLLM_CACHE_ROOT=str(cache/'vllm'),TRITON_CACHE_DIR=str(cache/'triton'))
os.execv(command[0],command)
