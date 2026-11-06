from __future__ import annotations
import copy,json,hashlib,shutil,tempfile,subprocess,unittest,uuid
from pathlib import Path
from validation.core import validate,canonical,digest,load,DIRECTORIES,archive_release,verify_release,VERSION
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=load(ROOT/'tests/fixtures/synthetic.json')

class ContentTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for name in ['schemas','policies']:shutil.copytree(ROOT/name,self.root/name)
  self.records=copy.deepcopy(FIXTURE['records']);self.deps=copy.deepcopy(FIXTURE['dependencies'])
 def tearDown(self):self.tmp.cleanup()
 def save(self):
  for name in ['data','editorial']:
   if (self.root/name).exists():shutil.rmtree(self.root/name)
  for x in self.records:
   p=self.root/DIRECTORIES[x['entityType']]/(x['id']+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canonical(x))
  (self.root/'dependencies.json').write_bytes(canonical(self.deps))
 def run_check(self,mode='authoring'):
  self.save();return validate(self.root,mode)
 def codes(self,v):return {d.ruleCode for d in v.issues if d.severity=='error'}
 def question(self,family='single-choice'):return next(x for x in self.records if x['entityType']=='question' and x['questionType']==family)
 def test_all_synthetic_question_families_structural(self):
  v=self.run_check();self.assertEqual(self.codes(v),set());self.assertTrue(any(d.ruleCode=='PUB-SYNTHETIC' for d in v.issues));self.assertEqual(sum(r['entityType']=='question' for r in v.records.values()),7)
 def test_production_metadata_has_no_structural_errors_but_is_not_approved(self):
  a=validate(ROOT);self.assertFalse(self.codes(a));b=validate(ROOT,'release');self.assertTrue({'PUB-RIGHTS','PUB-REPRODUCTION','GOVERNANCE-RELEASE','RESTRICTION-TRUST'}<=self.codes(b))
 def test_all_language_and_open_families_use_valid_rubric_contract(self):
  for family in ['word-form-identification','sentence-correction','sentence-construction','word-formation','grammatical-analysis','sanskrit-composition','long-answer','explanation','open-ended']:
   with self.subTest(family=family):
    q=self.question('translation');q['questionType']=family;self.assertFalse(self.codes(self.run_check()));q['questionType']='translation'
 def test_single_choice_rejects_multiple_keys(self):
  self.question()['evaluation']['correctOptionKeys']=['blue','red'];self.assertIn('QUESTION-SINGLE',self.codes(self.run_check()))
 def test_unknown_correct_key_rejected(self):
  self.question()['evaluation']['correctOptionKeys']=['absent'];self.assertIn('QUESTION-CHOICE',self.codes(self.run_check()))
 def test_duplicate_option_key_rejected(self):
  self.question()['options'][1]['key']='blue';self.assertIn('QUESTION-KEY',self.codes(self.run_check()))
 def test_boolean_requires_exactly_two_options(self):
  q=self.question('true-false');q['options'].append({'key':'maybe','textRef':q['options'][0]['textRef']});self.assertIn('QUESTION-BOOLEAN',self.codes(self.run_check()))
 def test_family_evaluation_mismatch(self):
  self.question('short-answer')['questionType']='long-answer';self.assertIn('QUESTION-EVALUATION',self.codes(self.run_check()))
 def test_wrong_component_type(self):
  self.question()['explanationRefs']=[self.question()['promptRef']];self.assertIn('REF-TYPE',self.codes(self.run_check()))
 def test_answer_dependency_cannot_be_an_agent(self):
  q=self.question();q['answerDependencies']=[{'id':self.records[0]['id'],'revision':1}];self.assertIn('REF-TYPE',self.codes(self.run_check()))
 def test_blank_keys_must_match_answers(self):
  self.question('fill-in-blanks')['evaluation']['blankAnswers'][0]['blankKey']='missing';self.assertIn('QUESTION-BLANKS',self.codes(self.run_check()))
 def test_blank_markers_must_exist_in_prompt(self):
  q=self.question('fill-in-blanks');next(r for r in self.records if r['id']==q['promptRef']['id'])['text']='No identified blank here';self.assertIn('QUESTION-BLANK-PROMPT',self.codes(self.run_check()))
 def test_matching_requires_valid_right_keys(self):
  self.question('matching')['evaluation']['pairs'][0]['rightKey']='absent';self.assertIn('QUESTION-MATCHING',self.codes(self.run_check()))
 def test_matching_requires_every_left_key_once(self):
  self.question('matching')['evaluation']['pairs'].pop();self.assertIn('QUESTION-MATCHING',self.codes(self.run_check()))
 def test_rubric_criteria_are_not_mcq_options(self):
  q=self.question('translation');q['options']=self.question()['options'];self.assertIn('QUESTION-FIELDS',self.codes(self.run_check()))
 def test_explicit_policy_required(self):
  del self.question('short-answer')['evaluation']['normalisationPolicyId'];self.assertIn('SCHEMA',self.codes(self.run_check()))
 def test_fuzzy_or_cross_script_policy_forbidden(self):
  self.question('short-answer')['evaluation']['normalisationPolicyId']='iast-equals-devanagari';self.assertIn('SCHEMA',self.codes(self.run_check()))
 def test_rubric_requires_manual_policy(self):
  self.question('translation')['evaluation']['normalisationPolicyId']='identity-v1';self.assertIn('QUESTION-POLICY',self.codes(self.run_check()))
 def test_pins_never_fall_back_to_latest(self):
  self.question()['promptRef']['revision']=2;self.assertIn('REF-MISSING',self.codes(self.run_check()))
 def test_missing_reference_rejected(self):
  self.question()['promptRef']['id']=str(uuid.uuid4());self.assertIn('REF-MISSING',self.codes(self.run_check()))
 def test_duplicate_identity_across_types_rejected(self):
  self.save();a=self.records[0];p=self.root/'editorial/reviews'/('duplicate.json');p.parent.mkdir(parents=True);p.write_bytes(canonical(a));self.assertIn('UUID-DUPLICATE',self.codes(validate(self.root)))
 def test_wrong_directory_and_filename_rejected(self):
  self.save();p=next((self.root/'data/questions').glob('*.json'));p.rename(p.with_name('wrong.json'));self.assertIn('FILE-NAME',self.codes(validate(self.root)))
  p=p.with_name('wrong.json');dest=self.root/'data/resources'/p.name;dest.parent.mkdir();p.rename(dest);self.assertIn('TYPE-DIRECTORY',self.codes(validate(self.root)))
 def test_membership_duplicate_order_rejected(self):
  ms=[r for r in self.records if r['entityType']=='collection-membership'];ms[1]['order']=ms[0]['order'];self.assertIn('MEMBERSHIP-DUPLICATE',self.codes(self.run_check()))
 def test_membership_does_not_accept_resource_or_copy(self):
  m=next(r for r in self.records if r['entityType']=='collection-membership');m['target']={'id':self.records[0]['id'],'revision':1};self.assertIn('REF-TYPE',self.codes(self.run_check()))
 def test_shared_content_cannot_depend_on_contextual_material(self):
  q=self.question();r=next(r for r in self.records if r['id']==q['promptRef']['id']);r['ownership']={'scope':'programme','programmeId':self.deps['records'][0]['id']};self.assertIn('OWNERSHIP',self.codes(self.run_check()))
 def test_derivation_cycles_rejected_but_owner_links_allowed(self):
  q=self.question();q['provenance']['inputRefs']=[q['promptRef']];r=next(r for r in self.records if r['id']==q['promptRef']['id']);r['provenance']['inputRefs']=[{'id':q['id'],'revision':1}];self.assertIn('PROVENANCE-CYCLE',self.codes(self.run_check()))
 def test_external_binding_without_payload_is_not_release_admission(self):
  self.assertFalse(self.codes(self.run_check()));self.assertIn('EXTERNAL-ADMISSION',self.codes(self.run_check('release')))
 def test_external_payload_wrong_hash_rejected(self):
  b=self.deps['records'][0];b['payloadPath']='dependencies/test.json';p=self.root/b['payloadPath'];p.parent.mkdir();p.write_bytes(canonical({'id':b['id'],'revision':1,'entityType':'grammar-concept'}));self.assertIn('EXTERNAL-DIGEST',self.codes(self.run_check()))
 def test_synthetic_release_denied(self):self.assertIn('PUB-SYNTHETIC',self.codes(self.run_check('release')))
 def test_no_author_set_approval_flag(self):
  self.question()['verified']=True;self.assertIn('SCHEMA',self.codes(self.run_check()))
 def test_unicode_roundtrip_preserves_combining_form_and_diacritics(self):
  r=next(r for r in self.records if r['entityType']=='text-representation');r['text']='naïve a\u0304 😀';v=self.run_check();self.assertFalse(self.codes(v));self.assertEqual(v.records[r['id']]['text'],'naïve a\u0304 😀')
 def test_duplicate_json_keys_and_invalid_utf8_rejected(self):
  self.save();p=next((self.root/'data/questions').glob('*.json'));p.write_bytes(b'{"id":1,"id":2}\n');self.assertIn('JSON-PARSE',self.codes(validate(self.root)));p.write_bytes(b'\xff');self.assertIn('JSON-PARSE',self.codes(validate(self.root)))
 def test_invalid_unicode_replacement_rejected(self):
  next(r for r in self.records if r['entityType']=='text-representation')['text']='bad\ufffd';self.assertIn('UNICODE-INVALID',self.codes(self.run_check()))
 def test_lone_surrogate_rejected_without_rewrite(self):
  self.save();p=next((self.root/'data/representations').glob('*.json'));v=load(p);v['text']='bad\ud800';p.write_text(json.dumps(v,ensure_ascii=True));self.assertIn('JSON-PARSE',self.codes(validate(self.root)))
 def test_formatting_rejected(self):
  self.save();p=next((self.root/'data/questions').glob('*.json'));p.write_text(json.dumps(load(p)));self.assertIn('JSON-FORMAT',self.codes(validate(self.root)))
 def test_unknown_schema_format_is_not_silently_ignored(self):
  self.save();p=self.root/'schemas/0.1.0/questions/question.schema.json';s=load(p);s['allOf'][1]['properties']['difficulty']['format']='made-up';p.write_bytes(canonical(s));self.assertIn('SCHEMA-BUNDLE',self.codes(validate(self.root)))
 def test_schema_refs_are_offline_and_cannot_fetch_network(self):
  self.save();p=self.root/'schemas/0.1.0/questions/question.schema.json';s=load(p);s['allOf'][0]['$ref']='https://invalid.example/schema';p.write_bytes(canonical(s));self.assertIn('SCHEMA-BUNDLE',self.codes(validate(self.root)))
 def media(self):
  base=copy.deepcopy(self.records[0]);base.update(id=str(uuid.uuid4()),entityType='media-asset',mediaKind='document',mimeType='application/pdf',fileName='sample.pdf',byteSize=9,sha256=digest(b'%PDF-test'),language='en',reproductionRightsId=self.records[1]['id'],storage={'kind':'local','path':'assets/documents/sample.pdf'},availability='available');base.pop('agentKind');base.pop('displayName');self.records.append(base);p=self.root/base['storage']['path'];p.parent.mkdir(parents=True);p.write_bytes(b'%PDF-test');base['byteSize']=p.stat().st_size;return base,p
 def test_missing_binary_rejected(self):
  m,p=self.media();p.unlink();self.assertIn('MEDIA-FILE',self.codes(self.run_check()))
 def test_wrong_asset_digest_and_size_rejected(self):
  m,p=self.media();m['sha256']='a'*64;self.assertIn('MEDIA-DIGEST',self.codes(self.run_check()))
 def test_mime_signature_and_extension_rejected(self):
  m,p=self.media();p.write_bytes(b'not a pdf');m['sha256']=digest(p.read_bytes());m['byteSize']=p.stat().st_size;self.assertIn('MEDIA-MIME',self.codes(self.run_check()))
 def test_media_kind_mime_mismatch(self):
  m,p=self.media();m['mediaKind']='image';self.assertIn('MEDIA-KIND',self.codes(self.run_check()))
 def test_draft_never_protects_uncleared_public_binary(self):
  self.media();self.assertIn('PUBLIC-ASSET-RIGHTS',self.codes(self.run_check()))
 def test_unregistered_binary_rejected(self):
  p=self.root/'assets/images/unknown.png';p.parent.mkdir(parents=True);p.write_bytes(b'fake');self.assertIn('MEDIA-UNTRACKED',self.codes(self.run_check()))
 def test_asset_path_traversal_rejected(self):
  m,p=self.media();m['storage']['path']='assets/../../private.pdf';self.assertIn('MEDIA-FILE',self.codes(self.run_check()))
 def test_external_uri_does_not_imply_reproduction_rights(self):
  m,p=self.media();p.unlink();m['storage']={'kind':'external','uri':'https://example.org/sample.pdf'};self.assertIn('PUB-REPRODUCTION',{d.ruleCode for d in self.run_check().issues})
 def test_external_uri_credentials_and_token_query_rejected(self):
  m,p=self.media();p.unlink();m['storage']={'kind':'external','uri':'https://user:password@example.org/file?token=private'};self.assertIn('MEDIA-URI-PRIVACY',self.codes(self.run_check()))
 def sidecar(self,kind='review-record'):
  target=self.question();r=copy.deepcopy(self.records[0]);r.pop('agentKind');r.pop('displayName');r.update(id=str(uuid.uuid4()),entityType=kind,targetRef={'id':target['id'],'revision':1},targetSha256=digest(canonical(target)))
  if kind=='review-record':r.update(reviewerRef={'id':self.records[0]['id'],'revision':1},reviewScope='pedagogical',decision='approved',reviewedAt='2026-11-06T10:00:00Z',rationale='Synthetic test decision, never actual approval.',dependencyRefs=[target['promptRef'],*target['knowledgeRefs'],*target['answerDependencies'],*[o['textRef'] for o in target['options']]])
  else:r.update(action='withdraw',recordedAt='2026-11-06T10:00:00Z',rationale='Synthetic withdrawal test.')
  r['dependencyRefs']=list({json.dumps(v,sort_keys=True):v for v in r['dependencyRefs']}.values()) if kind=='review-record' else []
  if kind!='review-record':r.pop('dependencyRefs',None)
  self.records.append(r);return r,target
 def test_self_review_is_not_approval(self):
  self.sidecar();self.assertIn('REVIEW-INDEPENDENCE',self.codes(self.run_check()))
 def test_review_digest_tampering_rejected(self):
  r,q=self.sidecar();r['targetSha256']='0'*64;self.assertIn('REVIEW-DIGEST',self.codes(self.run_check()))
 def test_review_omitted_answer_dependencies_rejected(self):
  r,q=self.sidecar();r['dependencyRefs']=[];self.assertIn('REVIEW-DEPENDENCIES',self.codes(self.run_check()))
 def test_invalid_datetime_rejected(self):
  r,q=self.sidecar();r['reviewedAt']='2026-02-30T10:00:00Z';self.assertIn('SCHEMA',self.codes(self.run_check()))
 def test_withdrawn_dependency_excludes_collection(self):
  self.sidecar('retirement-record');self.assertIn('PUB-RETIRED-DEPENDENCY',self.codes(self.run_check('release')))
 def init_git(self):
  for args in [['init','-b','main'],['config','user.name','Synthetic test'],['config','user.email','test@example.invalid'],['add','.'],['commit','-qm','Synthetic test snapshot']]:subprocess.run(['git',*args],cwd=self.root,check=True,capture_output=True)
 def test_changed_revision_must_increment(self):
  self.save();self.init_git();base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=self.root,text=True).strip();self.question()['difficulty']='advanced';self.save();self.assertIn('REVISION-NOT-INCREMENTED',self.codes(validate(self.root,base_commit=base)))
 def test_tooling_archive_is_reproducible_and_tampering_fails(self):
  self.save();self.init_git();a=self.root.parent/(self.root.name+'-release-a');b=self.root.parent/(self.root.name+'-release-b')
  try:
   first=archive_release(self.root,a,'0.1.0-test.1');second=archive_release(self.root,b,'0.1.0-test.1');self.assertEqual(first,second);self.assertEqual(first['members'],[]);self.assertEqual(verify_release(a)['mode'],'tooling')
   p=a/'snapshot/policies/registry.json';p.write_bytes(b'altered');self.assertRaises(ValueError,verify_release,a)
  finally:shutil.rmtree(a,ignore_errors=True);shutil.rmtree(b,ignore_errors=True)
 def test_release_never_overwrites_or_builds_dirty_snapshot(self):
  self.save();self.init_git();(self.root/'dirty.txt').write_text('change');self.assertRaises(ValueError,archive_release,self.root,self.root/'output','0.1.0')


class ReleaseResolutionTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def archive(self):
  # Symbolic software fixtures, never teaching content or a learner-ready release.
  ids=[str(uuid.uuid4()) for _ in range(2)];old={'id':ids[0],'revision':1,'entityType':'question','value':'old synthetic key'};new={**old,'revision':2,'value':'new synthetic key'};owner={'id':ids[1],'revision':1,'entityType':'question','answerDependencies':[{'id':ids[0],'revision':1}]}
  m={'members':[],'resolutionMap':{ids[0]:2,ids[1]:1}}
  for r in [old,new,owner]:
   path=f'records/{r["id"]}/{r["revision"]}.json';p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canonical(r));m['members'].append({'id':r['id'],'revision':r['revision'],'entityType':r['entityType'],'path':path,'sha256':digest(p.read_bytes())})
  return m,ids
 def test_old_answer_pin_survives_new_release_default(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();r=ReleaseResolver(self.root,m);self.assertEqual(r.resolve({'id':ids[0],'revision':1})['value'],'old synthetic key');self.assertEqual(r.resolve({'id':ids[0]})['value'],'new synthetic key')
 def test_missing_historical_bytes_never_substitute_current(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();(self.root/m['members'][0]['path']).unlink();self.assertRaises(ValueError,ReleaseResolver,self.root,m)
 def test_tampered_historical_payload_rejected(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();(self.root/m['members'][0]['path']).write_bytes(b'changed');self.assertRaises(ValueError,ReleaseResolver,self.root,m)
 def test_duplicate_member_rejected(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();m['members'].append(m['members'][0]);self.assertRaises(ValueError,ReleaseResolver,self.root,m)
 def test_unknown_or_missing_default_never_uses_current(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();del m['resolutionMap'][ids[0]];(self.root/m['members'][1]['path']).unlink();m['members'].pop(1);r=ReleaseResolver(self.root,m);self.assertRaises(ValueError,r.resolve,{'id':ids[0]});self.assertEqual(r.resolve({'id':ids[0],'revision':1})['revision'],1)
 def test_default_requires_exact_member(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();m['resolutionMap'][ids[0]]=99;self.assertRaises(ValueError,ReleaseResolver,self.root,m)
 def test_member_paths_cannot_escape_archive(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();m['members'][0]['path']='../../private.json';self.assertRaises(ValueError,ReleaseResolver,self.root,m)
 def test_orphan_historical_revision_rejected(self):
  from validation.resolution import ReleaseResolver
  m,ids=self.archive();owner=m['members'][-1];p=self.root/owner['path'];x=load(p);x['answerDependencies'][0]['revision']=2;p.write_bytes(canonical(x));owner['sha256']=digest(p.read_bytes());self.assertRaises(ValueError,ReleaseResolver,self.root,m)

if __name__=='__main__':unittest.main()
