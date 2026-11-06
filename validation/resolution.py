"""Immutable archive reference resolution, independent of current authoring files."""
from pathlib import Path
from .core import load,digest,references

class ReleaseResolver:
    def __init__(self,archive,manifest):
        self.archive=Path(archive).resolve();self.members={};self.defaults=manifest['resolutionMap'];self.types={}
        for m in manifest['members']:
            key=(m['id'],m['revision'])
            if key in self.members:raise ValueError('Duplicate exact release member')
            if m['id'] in self.types and self.types[m['id']]!=m['entityType']:raise ValueError('Permanent identity repurposed across types')
            self.types[m['id']]=m['entityType']
            expected=f'records/{m["id"]}/{m["revision"]}.json'
            if m['path']!=expected:raise ValueError('Member path must bind identity and revision')
            p=(self.archive/m['path']).resolve()
            if not p.is_relative_to(self.archive) or not p.is_file() or p.is_symlink():raise ValueError('Missing/unsafe exact archived member')
            data=p.read_bytes()
            if digest(data)!=m['sha256']:raise ValueError('Archived member digest mismatch')
            r=load(p)
            if not isinstance(r,dict) or any(r.get(k)!=m[k] for k in ['id','revision','entityType']):raise ValueError('Archived bytes do not match member identity/revision/type')
            self.members[key]=r
        for id,revision in self.defaults.items():
            if (id,revision) not in self.members:raise ValueError('Release default must resolve an exact member')
        critical=set()
        for r in self.members.values():
            for _,ref,_ in references(r):
                target=self.resolve(ref)
                if 'revision' in ref:critical.add((target['id'],target['revision']))
        for key in self.members:
            if self.defaults.get(key[0])!=key[1] and key not in critical:raise ValueError('Unreferenced non-default historical member')
    def resolve(self,ref):
        revision=ref.get('revision',self.defaults.get(ref['id']))
        key=(ref['id'],revision)
        if key not in self.members:raise ValueError('Reference unavailable in this exact release; no latest/main fallback')
        return self.members[key]
