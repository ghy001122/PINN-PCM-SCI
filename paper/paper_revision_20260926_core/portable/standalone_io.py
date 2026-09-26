"""Array-only I/O replacement for the old execution driver; no model imports."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'outputs/runs/20260925-fixed-temperature-phase-probe/frozen-config.json'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
class Resources:
    def __init__(self,*args):pass
    def check(self):pass
    def record(self):return dict(mode='saved-array CPU recomputation',models=0,optimizers=0,trajectory_steps=0)
