"""Offline validation for learning-content 0.1.0. Never grades learner responses."""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, re, subprocess, sys, unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlsplit
from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

VERSION='0.1.0'
DIRECTORIES={'agent':'data/agents','rights-statement':'data/rights','text-representation':'data/representations','source-work':'data/sources/works','source-edition':'data/sources/editions','source-reference':'data/sources/references','question':'data/questions','rubric':'data/rubrics','scholarly-component':'data/components','collection':'data/collections','collection-membership':'data/memberships','resource':'data/resources','media-asset':'data/media','review-record':'editorial/reviews','workflow-record':'editorial/workflow','retirement-record':'editorial/retirements'}
NS='urn:saakalyam:learning:0.1.0:'
FORMATS=FormatChecker()
@FORMATS.checks('date-time', raises=(ValueError, TypeError))
def date_time(value):
    if not isinstance(value,str):return True
    if not re.fullmatch(r'\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d(?:\.\d+)?(?:[Zz]|[+-]\d\d:\d\d)',value):return False
    datetime.datetime.fromisoformat(value.upper().replace('Z','+00:00'));return True
@FORMATS.checks('uri', raises=ValueError)
def uri(value):
    if not isinstance(value,str):return True
    if re.search(r'[\s\x00-\x1f<>"{}|\\^`]',value):return False
    u=urlsplit(value)
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9+.-]*',u.scheme):return False
    return bool(u.netloc) if u.scheme in ('http','https') else bool(u.path)

def canonical(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
def digest(value):return hashlib.sha256(value).hexdigest()
def pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('Duplicate JSON key: '+key)
        result[key]=value
    return result

def load(path):return json.loads(path.read_bytes().decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda v: (_ for _ in ()).throw(ValueError('Non-finite JSON number: '+v)))
def walk(value,path=''):
    yield path,value
    if isinstance(value,dict):
        for k,v in value.items():yield from walk(v,path+'/'+str(k).replace('~','~0').replace('/','~1'))
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from walk(v,path+'/'+str(i))

def references(record):
    # Declared ID fields plus exact ref objects; no suffix guessing or network resolution.
    id_fields={'rightsId':'rights-statement','reproductionRightsId':'rights-statement','agentId':'agent','ownerId':None,'collectionId':'collection','workId':'source-work','programmeId':'programme'}
    for path,v in walk(record):
        if isinstance(v,dict) and set(v)=={'id','revision'}:yield path,v,None
        elif path.rsplit('/',1)[-1] in id_fields and isinstance(v,str):yield path,{'id':v},id_fields[path.rsplit('/',1)[-1]]

@dataclass
class Diagnostic:
    severity:str
    ruleCode:str
    file:str
    entityId:str|None
    revision:int|None
    field:str
    message:str
    relatedRefs:list
    remediation:str

class Validator:
    def __init__(self,root,mode='authoring',base_commit=None):
        self.root=Path(root).resolve();self.mode=mode;self.base_commit=base_commit;self.issues=[];self.records={};self.paths={};self.raw={};self.external={};self.schemas={};self.config={}
    def issue(self,code,file,record=None,field='',message='',refs=None,severity='error',fix='Correct the record or keep it outside publication until the required evidence exists.'):
        self.issues.append(Diagnostic(severity,code,str(file),record.get('id') if isinstance(record,dict) else None,record.get('revision') if isinstance(record,dict) else None,field,message,refs or [],fix))
    def pending(self,code,file,r,field,msg,refs=None):self.issue(code,file,r,field,msg,refs,severity='error' if self.mode=='release' else 'warning')
    def safe(self,relative):
        p=self.root/relative
        if p.is_symlink() or not p.resolve().is_relative_to(self.root):raise ValueError('Path escapes repository or is a symlink: '+str(relative))
        return p
    def parse(self,p,formatting=True):
        rel=str(p.relative_to(self.root))
        try:
            if p.is_symlink():raise ValueError('Symbolic links are not content authority files')
            value=load(p)
            if formatting and canonical(value)!=p.read_bytes():self.issue('JSON-FORMAT',rel,value if isinstance(value,dict) else None,message='Use deterministic UTF-8, sorted keys, two spaces, LF and final newline.',fix='Run python -m validation format.')
            for path,v in walk(value):
                if isinstance(v,str):
                    if any(0xd800<=ord(c)<=0xdfff or c=='\ufffd' or (ord(c)<32 and c not in '\n\r\t') for c in v):self.issue('UNICODE-INVALID',rel,value if isinstance(value,dict) else None,path,'Ill-formed/replacement Unicode or unsupported control character; preserve and review original evidence.')
                    if any(unicodedata.bidirectional(c) in ('RLO','LRO','RLE','LRE','PDF','RLI','LRI','FSI','PDI') for c in v):self.issue('UNICODE-BIDI',rel,value if isinstance(value,dict) else None,path,'Bidi control characters require a reviewed contract; never silently remove them.')
            return value
        except (ValueError,UnicodeError,OSError) as e:
            self.issue('JSON-PARSE',rel,message=str(e));return None
    def setup(self):
        try:self.config=self.parse(self.root/'policies/registry.json')

        except (ValueError,OSError) as e:self.issue('POLICY-REGISTRY','policies/registry.json',message=str(e));return
        if not isinstance(self.config,dict):return
        registry=Registry()
        for p in sorted((self.root/'schemas/0.1.0').rglob('*.json')):
            try:
                s=self.parse(p);Draft7Validator.check_schema(s)
                for path,v in walk(s):
                    if isinstance(v,dict) and isinstance(v.get('format'), str) and v['format'] not in ('uri','date-time'):raise ValueError('Unknown/unimplemented format at '+path)
                    if isinstance(v,dict) and '$ref' in v and not v['$ref'].startswith(NS):raise ValueError('Schemas may resolve only this pinned offline bundle')
                if s['$id'] in self.schemas:raise ValueError('Duplicate schema ID')
                self.schemas[s['$id']]=s;registry=registry.with_resource(s['$id'],Resource(contents=s, specification=DRAFT7))
            except Exception as e:self.issue('SCHEMA-BUNDLE',str(p.relative_to(self.root)),message=str(e))
        self.registry=registry
        self.shape(self.config,'registry','policies/registry.json')
    def shape(self,r,kind,file):
        s=self.schemas.get(NS+kind)
        if s is None:self.issue('TYPE-UNKNOWN',file,r,message='Unknown entity/artifact type: '+str(kind));return False
        try:errors=sorted(Draft7Validator(s,registry=self.registry,format_checker=FORMATS).iter_errors(r),key=lambda e:str(e.path))
        except Exception as e:self.issue('SCHEMA-RESOLUTION',file,r if isinstance(r,dict) else None,message=str(e));return False
        for e in errors:self.issue('SCHEMA',file,r if isinstance(r,dict) else None,'/'+ '/'.join(map(str,e.path)),e.message)
        return not errors
    def resolve(self,ref):
        r=self.records.get(ref['id']) or self.external.get(ref['id'])
        return r if r and ('revision' not in ref or ref['revision']==r['revision']) else None
    def require_type(self,ref,kinds,r,file,path):
        target=self.resolve(ref)
        if target and target['entityType'] not in kinds:self.issue('REF-TYPE',file,r,path,'Target type must be one of '+', '.join(kinds),[ref])
        return target
    def approved(self,r,scope):
        expected=digest(self.raw.get(r['id'],canonical(r)))
        authorities=self.config.get('reviewAuthorities',[])
        inputs={json.dumps(ref,sort_keys=True) for _,ref,_ in references(r) if 'revision' in ref}
        for review in self.records.values():
            if review['entityType']!='review-record' or review['targetRef']!={'id':r['id'],'revision':r['revision']} or review['targetSha256']!=expected or review['reviewScope']!=scope:continue
            author_ids={a['agentId'] for a in r['attributions']}
            reviewer=review['reviewerRef']['id']
            if reviewer in author_ids:continue
            if not any(a.get('agentId')==reviewer and scope in a.get('scopes',[]) for a in authorities):continue
            if not inputs.issubset({json.dumps(p,sort_keys=True) for p in review['dependencyRefs']}):continue
            decisions=[v for v in self.records.values() if v['entityType']=='review-record' and v['targetRef']==review['targetRef'] and v['reviewScope']==scope]
            latest=max(decisions,key=lambda v:(v['reviewedAt'],v['id']))
            if latest['id']==review['id'] and review['decision']=='approved':return True
        return False
    def publication(self,r,file):
        t=r['entityType']
        if r['origin']=='synthetic':self.pending('PUB-SYNTHETIC',file,r,'/origin','Synthetic fixtures never qualify for learner delivery.')
        rights=self.resolve({'id':r['rightsId']})
        required={'question':'authored-learning','rubric':'authored-learning','scholarly-component':'authored-learning','resource':'catalogue-metadata','text-representation':'representation','source-work':'catalogue-metadata','source-edition':'catalogue-metadata','source-reference':'catalogue-metadata'}.get(t,'record-metadata')
        if rights and required not in rights.get('layers',[]):self.issue('RIGHTS-LAYER',file,r,'/rightsId','Rights metadata does not cover '+required,[{'id':rights['id'],'revision':rights['revision']}])
        if rights and (rights['basis']=='unknown' or not rights.get('evidence') or not self.approved(rights,'rights') or not {'reproduce','redistribute'}.issubset(rights.get('proposedUses',[]))):self.pending('PUB-RIGHTS',file,r,'/rightsId','No independently accepted rights evidence for this exact payload/use.')
        if not self.approved(r,'editorial') and t not in ('review-record','workflow-record','retirement-record'):self.pending('PUB-EDITORIAL',file,r,'','No independently appointed editorial approval of these exact bytes/dependencies.')
        if t in ('question','rubric','scholarly-component'):
            for scope in ('scholarly','pedagogical'):
                if not self.approved(r,scope):self.pending('PUB-'+scope.upper(),file,r,'','Missing independent '+scope+' review.')
            if not r['provenance']['sourceRefs'] and not r['provenance']['inputRefs']:self.pending('PUB-PROVENANCE',file,r,'/provenance','Answer/content evidence has not been supplied.')
        if r['origin'] in ('adapted','derived','transcribed','imported') and (not r['provenance']['inputRefs'] or not r['provenance'].get('method')):self.pending('PUB-LINEAGE',file,r,'/provenance','Material inputs and method must be pinned for imported/derived material.')
        if t in ('source-edition','media-asset'):
            material=self.resolve({'id':r['reproductionRightsId']})
            if material and ('source-material' not in material.get('layers',[]) or material['basis']=='unknown' or not self.approved(material,'rights') or not {'reproduce','redistribute'}.issubset(material.get('proposedUses',[]))):self.pending('PUB-REPRODUCTION',file,r,'/reproductionRightsId','Access/link does not establish reproduce/redistribute permission.')
        if t=='rights-statement' and r['basis']=='unknown':self.pending('PUB-UNKNOWN-RIGHTS',file,r,'/basis','Unknown rights is a disclosure, never a grant.')
        if t=='media-asset' and r['availability']!='available':self.pending('PUB-MEDIA-AVAILABILITY',file,r,'/availability','Unverified/unavailable media cannot be learner-release material.')
    def semantic(self,r,file):
        t=r['entityType']
        for path,ref,kind in references(r):
            target=self.resolve(ref)
            if not target:self.issue('REF-MISSING',file,r,path,'Missing exact referenced identity/revision; no latest/main fallback.',[ref]);continue
            if kind and target['entityType']!=kind:self.issue('REF-TYPE',file,r,path,'Expected '+kind,[ref])
            a,b=r['ownership'],target.get('ownership',{'scope':'shared'})
            if b['scope']=='programme' and (a['scope']!='programme' or a.get('programmeId')!=b.get('programmeId')):self.issue('OWNERSHIP',file,r,path,'Shared or cross-programme dependency would broaden contextual ownership.',[ref])
        if r['ownership']['scope']=='programme':self.require_type({'id':r['ownership']['programmeId']},['programme'],r,file,'/ownership/programmeId')
        for ref in r['provenance']['sourceRefs']:self.require_type(ref,['source-reference'],r,file,'/provenance/sourceRefs')
        if t=='question':self.question(r,file)
        if t=='rights-statement':
            for ref in r.get('rightsHolderRefs',[]):self.require_type(ref,['agent'],r,file,'/rightsHolderRefs')
        if t=='text-representation':
            owner=self.resolve({'id':r['ownerId']})
            if owner and owner['ownership']!=r['ownership']:self.issue('REP-OWNERSHIP',file,r,'/ownership','Representation and semantic owner must have identical scope.')
            if r['purpose'] not in ('component-text','label','transliteration'):self.issue('REP-SCOPE',file,r,'/purpose','Canonical lemma/source-text domains are not implemented here; use a validated external package.')
            if r['purpose']=='transliteration' and not r['provenance']['inputRefs']:self.issue('REP-INPUT',file,r,'/provenance/inputRefs','Transliteration must pin its actual input; no script equivalence is inferred.')
        if t=='resource':
            for ref in r['mediaRefs']:self.require_type(ref,['media-asset'],r,file,'/mediaRefs')
            for ref in r.get('programmeRefs',[]):self.require_type(ref,['programme'],r,file,'/programmeRefs')
            for ref in r.get('relatedQuestionRefs',[]):self.require_type(ref,['question'],r,file,'/relatedQuestionRefs')
            for ref in r.get('adaptationOfRefs',[]):self.require_type(ref,['resource'],r,file,'/adaptationOfRefs')
        if t=='media-asset':self.media(r,file)
        if t=='source-edition':
            self.require_type({'id':r['workId']},['source-work'],r,file,'/workId')
            for ref in r['basedOnEditionRefs']:self.require_type(ref,['source-edition'],r,file,'/basedOnEditionRefs')
        if t=='source-reference':
            self.require_type(r['editionRef'],['source-edition'],r,file,'/editionRef')
            expected={'page':['page'],'folio':['folio','side'],'uri-fragment':['fragment'],'amara-kanda-varga-verse':['kanda','varga','verse'],'ramayana-kanda-sarga-verse':['kanda','sarga','verse'],'panini-adhyaya-pada-sutra':['adhyaya','pada','sutra']}.get(r['locator']['scheme'])
            labels=[x['label'] for x in r['locator']['parts']]
            if len(labels)!=len(set(labels)) or (expected and labels!=expected):self.issue('SOURCE-LOCATOR',file,r,'/locator/parts','Locator labels/order do not match the declared source scheme.')
        if t in ('review-record','workflow-record','retirement-record'):
            target=self.resolve(r['targetRef'])
            if target and r['targetSha256']!=digest(self.raw.get(target['id'],canonical(target))):self.issue('REVIEW-DIGEST',file,r,'/targetSha256','Decision/sidecar does not bind the exact target bytes.',[r['targetRef']])
            if target and r['ownership']!=target['ownership']:self.issue('REVIEW-OWNERSHIP',file,r,'/ownership','Sidecar scope must match its target.')
            if t=='review-record':
                self.require_type(r['reviewerRef'],['agent'],r,file,'/reviewerRef')
                if target and r['reviewerRef']['id'] in [a['agentId'] for a in target['attributions']]:self.issue('REVIEW-INDEPENDENCE',file,r,'/reviewerRef','Required review cannot be self-certified.')
                if target:
                    actual={json.dumps(v,sort_keys=True) for _,v,_ in references(target) if 'revision' in v}
                    supplied={json.dumps(v,sort_keys=True) for v in r['dependencyRefs']}
                    if not actual.issubset(supplied):self.issue('REVIEW-DEPENDENCIES',file,r,'/dependencyRefs','Review omits a critical pinned dependency.')
        if t=='collection-membership':
            self.require_type({'id':r['collectionId']},['collection'],r,file,'/collectionId');self.require_type(r['target'],['question'],r,file,'/target')
        if t=='rubric':
            keys=[v['key'] for v in r['criteria']]
            if len(keys)!=len(set(keys)):self.issue('RUBRIC-KEY',file,r,'/criteria','Rubric criteria keys must be unique.')
            for v in r['criteria']:self.require_type(v['descriptionRef'],['text-representation'],r,file,'/criteria')
        if t=='scholarly-component':
            self.require_type(r['attachment'],['question','resource','rubric'],r,file,'/attachment')
            for ref in r['representationRefs']:self.require_type(ref,['text-representation'],r,file,'/representationRefs')
        self.publication(r,file)
    def question(self,r,file):
        family=r['questionType'];e=r['evaluation'];mode=e['mode']
        allowed={'single-choice':['choice-keys'],'multiple-select':['choice-keys'],'true-false':['choice-keys'],'fill-in-blanks':['blanks'],'matching':['matching'],'word-form-identification':['accepted-answers','rubric'],'sentence-correction':['accepted-answers','rubric'],'translation':['accepted-answers','rubric'],'sentence-construction':['accepted-answers','rubric'],'word-formation':['accepted-answers','rubric'],'grammatical-analysis':['accepted-answers','rubric'],'sanskrit-composition':['accepted-answers','rubric'],'short-answer':['accepted-answers','rubric'],'long-answer':['rubric'],'explanation':['rubric'],'open-ended':['rubric']}
        if mode not in allowed[family]:self.issue('QUESTION-EVALUATION',file,r,'/evaluation/mode','Question family and evaluation definition are incompatible.')
        self.require_type(r['promptRef'],['text-representation'],r,file,'/promptRef')
        for key in ('instructionRefs','explanationRefs','feedbackRefs'):
            for ref in r.get(key,[]):
                component=self.require_type(ref,['scholarly-component'],r,file,'/'+key)
                expected={'instructionRefs':'learning-instruction','explanationRefs':'learning-explanation','feedbackRefs':'learning-feedback'}[key]
                if component and component.get('entityType')=='scholarly-component' and (component['componentKind']!=expected or component['attachment']!={'id':r['id'],'revision':r['revision']}):self.issue('QUESTION-COMPONENT',file,r,'/'+key,'Component kind and exact attachment must match the question revision.')
        for ref in r['answerDependencies']:self.require_type(ref,['source-reference','text-representation','rubric','scholarly-component','vocabulary-entry','lexical-sense','grammar-concept','grammar-rule','dhatu','literary-unit'],r,file,'/answerDependencies')
        for ref in r['knowledgeRefs']:self.require_type(ref,['vocabulary-entry','lexical-sense','grammar-concept','grammar-rule','dhatu','literary-unit'],r,file,'/knowledgeRefs')
        for ref in r.get('topicRefs',[]):self.require_type(ref,['taxonomy-node'],r,file,'/topicRefs')
        def unique_keys(items,path):
            keys=[v['key'] for v in items]
            if len(set(keys))!=len(keys):self.issue('QUESTION-KEY',file,r,path,'Keys must be unique within this question revision.')
            for v in items:
                if 'textRef' in v:self.require_type(v['textRef'],['text-representation'],r,file,path)
            return set(keys)
        if mode=='choice-keys':
            options=r.get('options',[]);keys=unique_keys(options,'/options');answers=e['correctOptionKeys']
            if len(options)<2 or not set(answers)<=keys:self.issue('QUESTION-CHOICE',file,r,'/evaluation/correctOptionKeys','Correct keys must reference actual options.')
            if family in ('single-choice','true-false') and len(answers)!=1:self.issue('QUESTION-SINGLE',file,r,'/evaluation','Exactly one correct option is required.')
            if family=='true-false' and len(options)!=2:self.issue('QUESTION-BOOLEAN',file,r,'/options','True/false requires exactly two labelled options.')
            if e['normalisationPolicyId']!='identity-v1':self.issue('QUESTION-POLICY',file,r,'/evaluation','Choice keys use exact identity; text normalization is unrelated.')
        elif 'options' in r:self.issue('QUESTION-FIELDS',file,r,'/options','Options are only valid for choice families.')
        if mode=='accepted-answers':
            for ref in e['answerRefs']:self.require_type(ref,['text-representation'],r,file,'/evaluation/answerRefs')
        if mode=='blanks':
            keys=unique_keys(r.get('blanks',[]),'/blanks');answer_keys=[a['blankKey'] for a in e['blankAnswers']]
            if not keys or keys!=set(answer_keys) or len(answer_keys)!=len(set(answer_keys)):self.issue('QUESTION-BLANKS',file,r,'/evaluation/blankAnswers','Every identified blank must have exactly one accepted-variant list.')
            prompt=self.resolve(r['promptRef'])
            if prompt and set(re.findall(r'\{\{([A-Za-z0-9._-]+)\}\}',prompt.get('text','')))!=keys:self.issue('QUESTION-BLANK-PROMPT',file,r,'/promptRef','Prompt {{key}} markers must match identified blank keys.')
            for entry in e['blankAnswers']:
                for ref in entry['answerRefs']:self.require_type(ref,['text-representation'],r,file,'/evaluation/blankAnswers')
        elif 'blanks' in r:self.issue('QUESTION-FIELDS',file,r,'/blanks','Blank identifiers belong only to fill-in-blanks.')
        if mode=='matching':
            left=unique_keys(r.get('left',[]),'/left');right=unique_keys(r.get('right',[]),'/right');pairs=e['pairs'];mapped=[p['leftKey'] for p in pairs]
            if not left or not right or set(mapped)!=left or len(mapped)!=len(set(mapped)) or any(p['rightKey'] not in right for p in pairs):self.issue('QUESTION-MATCHING',file,r,'/evaluation/pairs','Map every left key exactly once to a valid right key; repeated right targets are allowed explicitly.')
            if e['normalisationPolicyId']!='identity-v1':self.issue('QUESTION-POLICY',file,r,'/evaluation','Matching uses exact local keys.')
        elif 'left' in r or 'right' in r:self.issue('QUESTION-FIELDS',file,r,'','Matching sides cannot be placed on another task family.')
        if mode=='rubric':
            self.require_type(e['rubricRef'],['rubric'],r,file,'/evaluation/rubricRef')
            if e['normalisationPolicyId']!='manual-review-v1':self.issue('QUESTION-POLICY',file,r,'/evaluation','Rubrics require manual review; no automatic equality judgement.')
        elif mode in ('accepted-answers','blanks') and e['normalisationPolicyId'] not in ('identity-v1','trim-edge-unicode-v1'):self.issue('QUESTION-POLICY',file,r,'/evaluation','Accepted text must name a supported explicit exact-comparison policy.')
    def media(self,r,file):
        mime=r.get('mimeType','');kind=r['mediaKind']
        expected='image' if mime.startswith('image/') else 'audio' if mime.startswith('audio/') else 'video' if mime.startswith('video/') else None
        if (expected and kind!=expected) or (mime=='application/pdf' and kind not in ('document','presentation')):self.issue('MEDIA-KIND',file,r,'/mediaKind','Media kind and MIME type disagree.')
        storage=r['storage']
        if storage['kind']=='external':
            u=urlsplit(storage['uri'])
            if u.username or u.password or u.query:self.issue('MEDIA-URI-PRIVACY',file,r,'/storage/uri','External URI must be a public stable HTTPS link without credentials or query tokens.')
            return
        try:
            p=self.safe(storage['path']);
            if not p.resolve().is_relative_to((self.root/'assets').resolve()):raise ValueError('Asset path must stay under assets/')
            blob=p.read_bytes()
            if len(blob)!=r['byteSize'] or digest(blob)!=r['sha256']:self.issue('MEDIA-DIGEST',file,r,'/storage/path','Local asset size or SHA-256 does not match metadata.')
            if len(blob)>1048576:self.issue('MEDIA-SIZE',file,r,'/byteSize','Initial ordinary-Git policy permits at most 1 MiB per asset; large media needs an approved storage decision.')
            signatures={'application/pdf':lambda b:b.startswith(b'%PDF-'),'image/png':lambda b:b.startswith(b'\x89PNG\r\n\x1a\n'),'image/jpeg':lambda b:b.startswith(b'\xff\xd8\xff'),'image/webp':lambda b:b[:4]==b'RIFF' and b[8:12]==b'WEBP','audio/wav':lambda b:b[:4]==b'RIFF' and b[8:12]==b'WAVE','text/plain':lambda b:True}
            extensions={'application/pdf':'.pdf','image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp','audio/wav':'.wav','text/plain':'.txt'}
            if r['mimeType'] not in signatures:self.issue('MEDIA-MIME-UNSUPPORTED',file,r,'/mimeType','Local format has no verified file-signature adapter; use an approved adapter before adding it.')
            elif not signatures[r['mimeType']](blob) or p.suffix.lower()!=extensions[r['mimeType']]:self.issue('MEDIA-MIME',file,r,'/mimeType','MIME, extension and verifiable file signature disagree.')
            if r['mimeType']=='text/plain':blob.decode('utf-8')
            if Path(r['fileName']).name!=p.name:self.issue('MEDIA-FILENAME',file,r,'/fileName','Filename must match the physical file, never its permanent identity.')
            material=self.records[r['reproductionRightsId']]
            if material['basis']=='unknown' or not material.get('evidence') or not self.approved(material,'rights') or 'redistribute' not in material.get('proposedUses',[]):self.issue('PUBLIC-ASSET-RIGHTS',file,r,'/reproductionRightsId','Do not put a rights-unresolved binary in public Git, including drafts.')
        except (OSError,ValueError,KeyError) as e:self.issue('MEDIA-FILE',file,r,'/storage/path',str(e))
    def history(self):
        if not self.base_commit:return
        if not re.fullmatch('[a-f0-9]{40}',self.base_commit):self.issue('GIT-BASE','',message='Base must be an exact Git commit SHA.');return
        result=subprocess.run(['git','ls-tree','-r','--name-only',self.base_commit,'--','data','editorial'],cwd=self.root,text=True,capture_output=True)
        if result.returncode:self.issue('GIT-BASE','',message='Base commit unavailable locally. Fetch exact history before validation.');return
        for name in result.stdout.splitlines():
            if not name.endswith('.json'):continue
            old_bytes=subprocess.check_output(['git','show',self.base_commit+':'+name],cwd=self.root)
            old=json.loads(old_bytes)
            current=self.records.get(old['id'])
            if not current:self.issue('REVISION-DELETED',name,old,message='Keep the identity; record retirement instead of deleting accepted records.');continue
            if current['entityType']!=old['entityType'] or current['ownership']!=old['ownership']:self.issue('IDENTITY-REPURPOSED',name,current,message='Type/ownership promotion cannot silently reuse the old identity.')
            if self.raw[current['id']]!=old_bytes and current['revision']<=old['revision']:self.issue('REVISION-NOT-INCREMENTED',self.paths[current['id']],current,'/revision','Changed payload requires an incremented revision.')
            if self.raw[current['id']]==old_bytes and current['revision']<old['revision']:self.issue('REVISION-REGRESSION',self.paths[current['id']],current,'/revision','Revision cannot decrease.')
    def run(self):
        self.setup()
        if any(x.severity=='error' for x in self.issues):return self.issues
        ext=self.parse(self.root/'dependencies.json')
        if ext and self.shape(ext,'dependencies','dependencies.json'):
            for binding in ext['records']:
                if binding['id'] in self.external:self.issue('EXTERNAL-DUPLICATE','dependencies.json',message='External identity has several default revisions.');continue
                # Binding is an exact external identity declaration, never canonical knowledge copied into a question.
                item={**binding,'ownership':{'scope':'shared'}}
                if 'payloadPath' in binding:
                    try:
                        payload=self.safe(binding['payloadPath']);body=load(payload)
                        if not isinstance(body,dict):raise ValueError('External payload must be an object.')
                        if digest(payload.read_bytes())!=binding['sha256'] or any(body.get(k)!=binding[k] for k in ['id','revision','entityType']):self.issue('EXTERNAL-DIGEST','dependencies.json',message='External binding and exact archived payload disagree.')
                        item={**body}
                    except (ValueError,OSError) as e:self.issue('EXTERNAL-PAYLOAD','dependencies.json',message=str(e))
                else:self.pending('PUB-EXTERNAL','dependencies.json',binding,'','External identity is declared but its exact validated package payload is unavailable.')
                self.external[binding['id']]=item
        for base in ('data','editorial'):
            for p in sorted((self.root/base).rglob('*.json')):
                r=self.parse(p);file=str(p.relative_to(self.root))
                if not isinstance(r,dict) or not self.shape(r,r.get('entityType') if isinstance(r,dict) else None,file):continue
                if p.parent != self.root/DIRECTORIES[r['entityType']]:self.issue('TYPE-DIRECTORY',file,r,message='Entity type belongs in '+DIRECTORIES[r['entityType']])
                if p.name!=r['id']+'.json':self.issue('FILE-NAME',file,r,message='Current authoring file must be named by UUID.json.')
                if r['id'] in self.records or r['id'] in self.external:self.issue('UUID-DUPLICATE',file,r,message='One independently maintained identity per current record, across all types.');continue
                self.records[r['id']]=r;self.paths[r['id']]=file;self.raw[r['id']]=p.read_bytes()
        if any(x.ruleCode in ('SCHEMA','JSON-PARSE') for x in self.issues):return self.issues
        for id,r in self.records.items():self.semantic(r,self.paths[id])
        memberships=[r for r in self.records.values() if r['entityType']=='collection-membership']
        for c in {r['collectionId'] for r in memberships}:
            ms=[r for r in memberships if r['collectionId']==c];orders=[r['order'] for r in ms];targets=[json.dumps(r['target'],sort_keys=True) for r in ms]
            if len(set(orders))!=len(orders) or len(set(targets))!=len(targets):self.issue('MEMBERSHIP-DUPLICATE','data/memberships',message='A collection cannot duplicate order or exact question membership.')
        # Cycles are forbidden only in evidence/derivation/edition lineage, not owner/representation back-links.
        def visit(id,trail,done):
            if id in trail:self.issue('PROVENANCE-CYCLE',self.paths[id],self.records[id],'/provenance/inputRefs','Circular material derivation is not independent evidence.');return
            if id in done:return
            r=self.records[id];refs=r['provenance']['inputRefs']+r.get('basedOnEditionRefs',[])+r.get('adaptationOfRefs',[])
            for ref in refs:
                if ref['id'] in self.records:visit(ref['id'],trail|{id},done)
            done.add(id)
        done=set()
        for id in self.records:visit(id,set(),done)
        retired={r['targetRef']['id'] for r in self.records.values() if r['entityType']=='retirement-record'}
        for id in retired:
            for r in self.records.values():
                if r['entityType'] not in ('retirement-record','review-record','workflow-record') and any(ref['id']==id for _,ref,_ in references(r)):self.pending('PUB-RETIRED-DEPENDENCY',self.paths[r['id']],r,'','Retired/withdrawn target remains a dependency; exclude or revise downstream use.')
        # Every binary in the public asset tree must be explicitly accounted for.
        accounted={r['storage']['path'] for r in self.records.values() if r['entityType']=='media-asset' and r['storage']['kind']=='local'}
        for p in (self.root/'assets').rglob('*'):
            if p.is_file() and str(p.relative_to(self.root)) not in accounted:self.issue('MEDIA-UNTRACKED',str(p.relative_to(self.root)),message='Unregistered asset cannot be silently published.')
        self.history()
        if self.mode=='release':
            if not self.config.get('learnerReleaseEnabled'):self.issue('GOVERNANCE-RELEASE','policies/registry.json',message='Learner releases remain disabled until licensing, reviewer appointments, public-draft terms and restriction policy are approved.')
            for binding in self.external.values():self.issue('EXTERNAL-ADMISSION','dependencies.json',binding,message='External knowledge requires its own validated, reviewed release adapter before learner admission; not inferred from an ID/hash binding.')
            for id in retired:self.issue('PUB-RETIRED',self.paths[id] if id in self.paths else 'editorial/retirements',self.records.get(id),message='Retired/withdrawn content is excluded from learner releases.')
            self.issue('RESTRICTION-TRUST','policies/registry.json',message='A trusted current restriction snapshot and freshness policy are not configured; no learner export is allowed.')
        return self.issues

def validate(root,mode='authoring',base_commit=None):
    v=Validator(root,mode,base_commit);v.run();return v

def archive_release(root,destination,version,mode='tooling'):
    root=Path(root).resolve();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Release path already exists; never overwrite a version.')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?',version):raise ValueError('Invalid dataset version.')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=root,text=True).strip():raise ValueError('Freeze a clean committed snapshot before creating release artifacts.')
    v=validate(root,'authoring' if mode=='tooling' else 'release')
    if any(x.severity=='error' for x in v.issues):raise ValueError('Validation failed; no release built: '+', '.join(sorted({x.ruleCode for x in v.issues if x.severity=='error'})))
    if mode!='tooling':raise ValueError('Learner release assembly is intentionally blocked pending external-package and restriction-trust admission.')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',commit],cwd=root,text=True).splitlines()
    files=[]
    # Tooling releases contain schemas, validator, policies, docs and tests only; no editorial corpus/assets.
    names=[n for n in names if not n.startswith(('data/','editorial/','assets/','dependencies/','releases/'))]
    for name in sorted(names):
        b=subprocess.check_output(['git','show',commit+':'+name],cwd=root);files.append({'path':name,'sha256':digest(b)})
    manifest={'schemaVersion':VERSION,'datasetVersion':version,'mode':'tooling','baseGitCommit':commit,'members':[],'resolutionMap':{},'files':files,'reviewDependencies':[],'assetDigests':[],'validation':{'errors':0,'validatorVersion':VERSION,'mode':'tooling'},'attributionNotices':['Existing source credits remain on metadata records; no source media is part of this tooling archive.'],'rightsNotices':['Licensing decisions remain pending. Public availability is not a redistribution/adaptation grant for Pravesha source content.'],'limitations':['Tooling snapshot only; no learner content release, approved question, media binary or publication rights asserted.']}
    v.shape(manifest,'manifest','manifest.json')
    if any(x.severity=='error' for x in v.issues):raise ValueError('Manifest failed schema validation.')
    destination.mkdir(parents=True)
    for name in names:
        p=destination/'snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show',commit+':'+name],cwd=root))
    (destination/'manifest.json').write_bytes(canonical(manifest));return manifest

def verify_release(path):
    path=Path(path).resolve();m=load(path/'manifest.json');root=path/'snapshot';v=Validator(root);v.setup();v.shape(m,'manifest','manifest.json')
    if m.get('mode')!='tooling':
        from .resolution import ReleaseResolver
        ReleaseResolver(path,m)
        raise ValueError('Exact archive resolution is separate from learner admission; an approved external-package/restriction-trust adapter is still required.')
    for f in m['files']:
        p=(root/f['path']).resolve()
        if not p.is_relative_to(root.resolve()) or not p.is_file() or digest(p.read_bytes())!=f['sha256']:raise ValueError('Missing, unsafe or altered release file: '+f['path'])
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    if actual!={f['path'] for f in m['files']}:raise ValueError('Archive has unmanifested or duplicate members.')
    if len(m['files'])!=len(actual):raise ValueError('Duplicate release file membership.')
    if any(d.severity=='error' for d in v.issues):raise ValueError('Release manifest/schema invalid.')
    return m

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',default='.');sub=parser.add_subparsers(dest='command',required=True)
    check=sub.add_parser('validate');check.add_argument('--mode',choices=['authoring','release'],default='authoring');check.add_argument('--base-commit');check.add_argument('--json',action='store_true')
    sub.add_parser('format')
    build=sub.add_parser('release');build.add_argument('--version',required=True);build.add_argument('--output',required=True);build.add_argument('--mode',choices=['tooling','learner'],default='tooling')
    verify=sub.add_parser('verify-release');verify.add_argument('path')
    args=parser.parse_args(argv)
    if args.command=='validate':
        v=validate(args.root,args.mode,args.base_commit)
        if args.json:print(json.dumps([asdict(d) for d in v.issues],ensure_ascii=False,indent=2))
        else:
            for d in v.issues:print(f'{d.severity.upper()} {d.ruleCode} {d.file} {d.entityId or "-"}@{d.revision or "-"} {d.field}: {d.message} Remediation: {d.remediation}')
            print(f'{len(v.records)} records; {sum(d.severity=="error" for d in v.issues)} errors; {sum(d.severity=="warning" for d in v.issues)} publication warnings. Structural validity is not approval.')
        return 1 if any(d.severity=='error' for d in v.issues) else 0
    try:
        if args.command=='format':
            root=Path(args.root)
            for base in ('data','editorial','schemas','policies','tests/fixtures'):
                for p in (root/base).rglob('*.json'):p.write_bytes(canonical(load(p)))
            p=root/'dependencies.json';p.write_bytes(canonical(load(p)))
        elif args.command=='release':print(json.dumps(archive_release(args.root,args.output,args.version,args.mode),indent=2))
        else:print('Verified tooling release '+verify_release(args.path)['datasetVersion'])
    except (ValueError,OSError,subprocess.SubprocessError) as e:print(str(e),file=sys.stderr);return 1
    return 0
