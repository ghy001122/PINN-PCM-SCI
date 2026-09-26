"""Lossless temporary NPY maps, bounded by live consumers, no metric changes."""
from pathlib import Path
import hashlib,shutil,weakref,zipfile,gc
import numpy as np
ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'temporary-array-storage'
ENTRIES={}
def arrays(path):
    path=Path(path).resolve()
    if not path.is_relative_to(ROOT):raise ValueError('Input escapes standalone root: '+str(path))
    if not path.is_file():raise FileNotFoundError(path)
    gc.collect()
    for key,(folder,refs) in list(ENTRIES.items()):
        if all(ref() is None for ref in refs):
            if not folder.resolve().is_relative_to(CACHE.resolve()):raise ValueError('cache containment')
            shutil.rmtree(folder);del ENTRIES[key]
    key=hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:20]
    folder=CACHE/key;folder.mkdir(parents=True,exist_ok=True)
    refs=ENTRIES.setdefault(key,(folder,[]))[1];values={}
    with zipfile.ZipFile(path) as z:
        for name in ('x','z','time','potential','temperature','phase','joule_density'):
            member=name+'.npy'
            if member not in z.namelist():
                if name=='joule_density':continue
                raise ValueError('Missing field '+name+' in '+str(path))
            q=folder/member
            if not q.exists():
                with z.open(member) as src,q.open('xb') as dst:shutil.copyfileobj(src,dst,4*1024*1024)
            a=np.load(q,mmap_mode='r',allow_pickle=False);refs.append(weakref.ref(a));values[name]=a
    return {k:values[k] for k in ('x','z','time','potential','temperature','phase')},values.get('joule_density')
