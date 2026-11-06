"""Public-file preflight. Human disclosure review remains necessary."""
from pathlib import Path
import json,re,subprocess,sys
from .core import load,canonical
from .identity import privacy_issues,assert_public_text

def audit(root):
 root=Path(root).resolve();errors=[];reviewed=[]
 result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root,capture_output=True)
 names=[n for n in result.stdout.decode().split('\0') if n] if result.returncode==0 else [str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not set(p.relative_to(root).parts)&{'.git','.local','.venv','__pycache__'}]
 for name in sorted(set(names)):
  p=root/name
  if p.is_symlink():errors.append(name+': symlink must not be published');continue
  if p.suffix.lower() in ('.pdf','.webp','.png','.jpg','.jpeg','.mp3','.mp4','.wav','.ppt','.pptx','.sqlite','.db','.zip','.exe'):errors.append(name+': binary/database absent from the approved initial publication scope');continue
  try:
   text=p.read_text(encoding='utf-8')
   if re.search(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}',text):errors.append(name+': potential credential')
   if re.search(r'/(?:Users|home)/[^/\s]+/',text):errors.append(name+': local home path must stay private')
   if p.suffix=='.json':
    x=load(p)
    if name.startswith(('data/','editorial/')) and privacy_issues(x):errors.append(name+': private identity/editorial information')
    if isinstance(x,dict) and x.get('format')=='saakalyam-attribution-v1':assert_public_text(x)
    if p.read_bytes()!=canonical(x):errors.append(name+': non-deterministic JSON')
   reviewed.append({'path':name,'bytes':p.stat().st_size})
  except (ValueError,UnicodeError,OSError):errors.append(name+': UTF-8/JSON or public-data check failed; inspect locally without logging input values.')
 return reviewed,errors

def main():
 reviewed,errors=audit('.')
 for e in errors:print('ERROR '+e)
 print(str(len(reviewed))+' UTF-8 files inspected; '+str(len(errors))+' preflight errors. No binary publication permitted in this initial scope. Human rights/privacy review remains separate.')
 return bool(errors)
if __name__=='__main__':raise SystemExit(main())
