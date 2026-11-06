"""Inventory only declared Pravesha learning files; never reads learner data or changes the app."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def canonical(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def inventory(app):
 app=Path(app).resolve();p=json.loads((app/'src/data/learning/pravesha.json').read_text())['programmes'][0]
 legacy=json.loads((app/'src/data/learning/legacy-resource-inventory.json').read_text())
 asset_manifest=json.loads((app/'public/learning/sbpr/asset-manifest.json').read_text())
 declared_images={slide['image']:slide for a in asset_manifest.values() for slide in a.get('slides',[])}
 rows=[];seen=set();image_links={s['image']:(l,s) for l in p['lessons'] for s in l['slides']}
 for a in p['assets']:
  file=app/'public'/a['href'].lstrip('/');b=file.read_bytes()
  if sha(b)!=a['sha256'] or len(b)!=a['bytes'] or not b.startswith(b'%PDF-'):raise ValueError('PDF identity/size/header drift: '+a['href'])
  seen.add(file.resolve());lessons=[{'lessonId':l['id'],'chapter':l['chapter'],'part':l['part']} for l in p['lessons'] if l.get('assetId')==a['id']]
  rows.append({'kind':'original-pdf','existingAssetId':a['id'],'path':str(file.relative_to(app)),'filename':file.name,'mimeType':'application/pdf','byteSize':len(b),'sha256':sha(b),'pagesDeclaredByApp':a['pages'],'association':lessons or [{'role':'thematic-workbook' if 'abhyash' in file.name else 'supplementary-resource','chapterMapping':'not inferred'}],'sourceUrl':a['sourceUrl'],'attribution':a['attribution'],'origin':'original-file-preserved','rights':'Access/link recorded; reproduction, redistribution, adaptation and licence obligations unresolved.','recommendation':'Do not publish binary; retain candidate asset ID after review; metadata-only linking may be proposed.'})
 for file in sorted((app/'public/learning').rglob('*')):
  if not file.is_file() or file.resolve() in seen:continue
  b=file.read_bytes();rel='/'+str(file.relative_to(app/'public'));link=image_links.get(rel)
  if file.suffix=='.webp':
   if not (b[:4]==b'RIFF' and b[8:12]==b'WEBP'):raise ValueError('Image signature drift: '+rel)
   if rel not in declared_images or sha(b)!=declared_images[rel]['sha256']:raise ValueError('Asset manifest image hash drift: '+rel)
   if link and sha(b)!=link[1]['sha256']:raise ValueError('Declared slide hash drift: '+rel)
   rows.append({'kind':'derived-slide-image','path':str(file.relative_to(app)),'filename':file.name,'mimeType':'image/webp','byteSize':len(b),'sha256':sha(b),'association':{'lessonId':link[0]['id'],'chapter':link[0]['chapter'],'part':link[0]['part'],'logicalSlide':link[1]['number'],'sourcePage':link[1]['sourcePage']} if link else {'role':'supplementary-first-practice-class' if file.name.startswith('abhvarga01-') else 'unmapped; human review required'},'source':'Rendered from a locally preserved original presentation; source-page links retained in app metadata where supplied.','attribution':p['attribution'],'origin':'derived','rights':'Rendering does not grant reproduction, redistribution or adaptation rights.','recommendation':'Do not copy; future UUIDv4 allocation after identity/source/rights review.'})
  elif file.name=='asset-manifest.json':rows.append({'kind':'asset-manifest-metadata','path':str(file.relative_to(app)),'byteSize':len(b),'sha256':sha(b),'origin':'application-generated-metadata','rights':'Not a source licence or subject review.','recommendation':'Retain as migration evidence; do not copy its source text or treat metadata as approved rights.'})
  else:raise ValueError('Unclassified local learning file requires inventory review: '+str(file.relative_to(app)))
 for l in p['lessons']:
  status=l.get('materialStatus','adapted-reading')
  rows.append({'kind':'lesson-metadata','lessonId':l['id'],'chapter':l['chapter'],'part':l['part'],'format':status,'assetId':l.get('assetId'),'sourceResourceIdentity':l.get('sourceResourceIdentity','not individually recorded'),'adaptedTextPresent':status=='adapted-reading','sourceTemplate':p['sourceTemplate'],'origin':'adaptation' if status=='adapted-reading' else 'source-reference','rights':'Source and adaptation rights/review unresolved; text not reproduced in this inventory.','recommendation':'Keep programme composition outside this repository increment; retain identity as a candidate reference, not a new canonical lesson.'})
  rows.append({'kind':'external-recording','uri':l['recordingUrl'],'association':{'lessonId':l['id'],'chapter':l['chapter'],'part':l['part']},'origin':'external-reference','attribution':'Linked by Saakalyam companion course; recording author/permissions not independently verified.','rights':'External link is not permission to download, redistribute or adapt.','recommendation':'Safe link metadata proposal only; verify availability, captions and rights separately.'})
 for item in p['supplementaryRecordings']:
  rows.append({'kind':'external-recording','uri':item['url'],'association':{'role':'supplementary','sourceIdentity':item['sourceIdentity']},'origin':'external-reference','attribution':'Linked by Saakalyam companion course; no independent creator/right-holder determination.','rights':'Access/link only; reproduction/redistribution/adaptation unresolved.','recommendation':'Metadata only; do not invent chapter membership.'})
 for rec in legacy['records']:
  if rec.get('legacyCourse')=='SBPR' and any(a['url']=='#' for a in rec['links']):rows.append({'kind':'unavailable-presentation-placeholder','sourceIdentity':rec['originalIdentity'],'chapter':rec['chapterAssociation'],'availability':'unavailable','origin':'source-placeholder','rights':'No presentation payload exists here to assess.','recommendation':'Remain unavailable. Allocate no MediaAsset/Resource or fabricated file.'})
 questions=[]
 for file in sorted((app/'src/data/learning/question-bank').glob('chapter-*.json'),key=lambda p:int(p.stem.split('-')[1])):
  b=file.read_bytes();q=json.loads(b);families={}
  for item in q['questions']:families[item['questionType']]=families.get(item['questionType'],0)+1
  questions.append({'chapter':q['chapter'],'path':str(file.relative_to(app)),'packageSha256':sha(b),'available':len(q['questions']),'sourceRecords':q['sourceQuestionCount'],'excluded':len(q['unresolved']),'families':families,'questionRevisions':sorted(set(r['revision'] for r in q['questions'])),'programmeId':q['programmeId'],'setId':q['setId'],'rightsStatus':q['rightsStatus'],'sourceCommit':q['sourceCommit'],'sources':[{'path':r['path'],'sha256':r['sha256']} for r in q['sources']],'recommendation':'No question/answer payload migration; retain identity candidates and exact source ledger after human rights/evidence/review reconciliation.'})
 counts={k:sum(r['kind']==k for r in rows) for k in sorted(set(r['kind'] for r in rows))}
 return {'inventoryVersion':'0.1.0','inspectedApplicationCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=app,text=True).strip(),'notice':'Inspection of actual current working files, including prior uncommitted app work. Facts/hashes/short credits only; no source passages, questions, keys, adapted teaching text, credentials or learner data. No file copied or external media fetched.','programmeId':p['programmeId'],'counts':counts,'localAudioFiles':0,'localVideoFiles':0,'questionTotals':{'available':sum(q['available'] for q in questions),'excluded':sum(q['excluded'] for q in questions),'sourceRecords':sum(q['sourceRecords'] for q in questions)},'resources':rows,'questionPackages':questions}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--app',required=True);ap.add_argument('--output',required=True);args=ap.parse_args();result=inventory(args.app);p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canonical(result));print(json.dumps({'resources':result['counts'],'questions':result['questionTotals']},indent=2))
if __name__=='__main__':main()
