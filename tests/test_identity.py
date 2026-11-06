"""Synthetic English identity cases; nobody here is a real contributor/reviewer."""
import copy
import json
import shutil
import subprocess
import unittest
import uuid
from unittest.mock import patch
from pathlib import Path
from tests import test_content as content_tests
ROOT=content_tests.ROOT
from validation.core import canonical, digest, load, validate, references, archive_release, verify_release
from validation.attribution import working_report, release_report, markdown
from validation.identity import REVIEW_TYPES


class ContributorTests(unittest.TestCase):
    setUp=content_tests.ContentTests.setUp
    tearDown=content_tests.ContentTests.tearDown
    save=content_tests.ContentTests.save
    run_check=content_tests.ContentTests.run_check
    codes=content_tests.ContentTests.codes
    question=content_tests.ContentTests.question
    init_git=content_tests.ContentTests.init_git

    def agent(self,kind='person',name='Synthetic test participant'):
        a=copy.deepcopy(self.records[0]);a.update(id=str(uuid.uuid4()),agentKind=kind,displayName=name)
        self.records.append(a);return a

    def credit(self,agent,role):return {'agentId':agent['id'],'role':role}

    def review(self,category='scholarly',target=None):
        q=target or self.question();a=self.agent(name='Synthetic independent reviewer')
        r=copy.deepcopy(self.records[0]);r.pop('agentKind');r.pop('displayName')
        r.update(id=str(uuid.uuid4()),entityType='review-record',targetRef={'id':q['id'],'revision':q['revision']},targetSha256=digest(canonical(q)),reviewerRef={'id':a['id'],'revision':1},reviewScope=category,reviewType=REVIEW_TYPES[category][0],reviewerRole=REVIEW_TYPES[category][1],scope={'kind':'whole-record'},decision='approved',reviewedAt='2026-11-06T10:00:00Z',rationale='Synthetic software review only; no scholarly approval.',dependencyRefs=list({json.dumps(ref,sort_keys=True):ref for _,ref,_ in references(q) if 'revision' in ref}.values()))
        self.records.append(r);return r,q

    def appoint(self,review):
        p=self.root/'policies/registry.json';s=load(p);s['reviewAuthorities'].append({'agentId':review['reviewerRef']['id'],'scopes':[review['reviewScope']]});p.write_bytes(canonical(s))

    def report_row(self,id):return next(r for r in working_report(self.root)['records'] if r['id']==id)

    def test_author_and_editor_survive_projection(self):
        q=self.question();author=copy.deepcopy(q['attributions'][0]);editor=self.agent();q['attributions'].append(self.credit(editor,'editor'))
        self.assertFalse(self.codes(self.run_check()));row=self.report_row(q['id']);self.assertEqual({a['role'] for a in row['attributions']},{'author','editor'});self.assertIn(author,q['attributions'])

    def test_multiple_roles_pseudonym_organisation_and_same_name_remain_distinct(self):
        q=self.question();a=self.agent('pseudonym','Synthetic shared display');b=self.agent('organisation','Synthetic shared display')
        q['attributions'] += [self.credit(a,'translator'),self.credit(a,'annotator'),self.credit(b,'contributor')]
        self.assertFalse(self.codes(self.run_check()));row=self.report_row(q['id']);self.assertEqual(len(row['attributions']),4);self.assertNotEqual(a['id'],b['id'])

    def test_display_name_change_keeps_identity_and_increments_revision(self):
        self.save();self.init_git();base=self.git_head();a=self.records[0];id=a['id'];a['displayName']='Synthetic preferred pseudonym';a['revision']=2;self.save()
        self.assertFalse(self.codes(validate(self.root,base_commit=base)));self.assertEqual(a['id'],id)

    def test_unknown_historical_author_has_no_fictional_agent(self):
        q=self.question();q['attributions']=[{'role':'author','attributionStatus':'unknown','note':'Legacy source does not identify an author.'}]
        self.assertFalse(self.codes(self.run_check()));row=self.report_row(q['id']);self.assertIsNone(row['attributions'][0]['agent']);self.assertIn('unknown',canonical(row).decode())
        q['attributions'][0]['agentId']=self.records[0]['id'];self.assertIn('SCHEMA',self.codes(self.run_check()))

    def test_unknown_requires_qualification_and_known_requires_agent(self):
        for credit in [{'role':'author','attributionStatus':'unknown'},{'role':'author','note':'No reference'}]:
            with self.subTest(credit=credit):self.question()['attributions']=[credit];self.assertIn('SCHEMA',self.codes(self.run_check()))

    def test_duplicate_role_agent_rejected_despite_note_change(self):
        q=self.question();q['attributions'].append({**q['attributions'][0],'note':'A second entry is still a duplicate.'});self.assertIn('ATTRIBUTION-DUPLICATE',self.codes(self.run_check()))

    def test_adaptation_keeps_original_author_source_and_translator(self):
        q=self.question();source=self.question('short-answer');original=copy.deepcopy(q['attributions'][0]);translator=self.agent();q.update(origin='adapted');q['provenance'].update(inputRefs=[{'id':source['id'],'revision':1}],method='Synthetic adaptation with original source preserved.');q['attributions'].append(self.credit(translator,'translator'))
        self.assertFalse(self.codes(self.run_check()));row=self.report_row(q['id']);self.assertIn(original,q['attributions']);self.assertEqual(row['provenance']['inputRefs'][0]['id'],source['id'])

    def git_head(self):return subprocess.check_output(['git','rev-parse','HEAD'],cwd=self.root,text=True).strip()

    def bump(self,q):
        q['revision']+=1
        for r in self.records:
            if r['entityType']=='collection-membership' and r['target']['id']==q['id']:r['target']['revision']=q['revision'];r['revision']+=1

    def test_correction_adds_editor_without_overwriting_author_or_translator(self):
        q=self.question();translator=self.agent();q['attributions'].append(self.credit(translator,'translator'));self.save();self.init_git();base=self.git_head();editor=self.agent();self.bump(q);q['difficulty']='advanced';q['attributions'].append(self.credit(editor,'editor'));self.save()
        self.assertFalse(self.codes(validate(self.root,base_commit=base)));q['attributions']=[self.credit(editor,'author')];self.save();self.assertIn('ATTRIBUTION-PRESERVATION',self.codes(validate(self.root,base_commit=base)))

    def test_explicit_evidenced_attribution_correction_is_possible(self):
        q=self.question();self.save();self.init_git();base=self.git_head();self.bump(q);q['attributions']=[{'role':'author','attributionStatus':'unknown','note':'Earlier synthetic attribution was unsupported.'}];q['provenance']['attributionCorrection']={'previousRevision':1,'reason':'Synthetic evidence corrects earlier credit.','evidenceRefs':[{'id':self.records[1]['id'],'revision':1}]};self.save();self.assertFalse(self.codes(validate(self.root,base_commit=base)))

    def test_exact_review_digest_revision_and_category(self):
        r,q=self.review('technical');self.appoint(r);v=self.run_check();self.assertFalse(self.codes(v));self.assertTrue(v.approved(q,'technical'));self.assertFalse(v.approved(q,'scholarly'))
        r['targetSha256']='0'*64;self.assertIn('REVIEW-DIGEST',self.codes(self.run_check()));self.assertRaises(ValueError,working_report,self.root)

    def test_old_review_retained_but_not_carried_forward_after_revision(self):
        r,q=self.review();self.appoint(r);self.save();self.init_git();base=self.git_head();self.bump(q);q['difficulty']='advanced';self.save();v=validate(self.root,base_commit=base);self.assertFalse(self.codes(v));self.assertFalse(v.approved(q,'scholarly'))
        review=self.report_row(q['id'])['reviews'][0];self.assertTrue(review['bindingValid']);self.assertFalse(review['appliesToDisplayedRevision']);self.assertEqual(review['targetRef']['revision'],1)

    def test_historical_reviewer_name_is_exact_not_current_profile(self):
        r,q=self.review();self.save();self.init_git();a=next(a for a in self.records if a['id']==r['reviewerRef']['id']);a['displayName']='Synthetic renamed reviewer';a['revision']=2;self.save();self.assertFalse(self.codes(validate(self.root)));review=self.report_row(q['id'])['reviews'][0];self.assertEqual(review['reviewer']['displayName'],'Synthetic independent reviewer')

    def test_missing_history_never_uses_current_bytes(self):
        r,q=self.review();self.bump(q);self.assertIn('REF-MISSING',self.codes(self.run_check()))

    def test_all_review_types_outcomes_and_legacy_mapping(self):
        for category in REVIEW_TYPES:
            for decision in ['approved','changes-requested','rejected','disputed','unable-to-determine']:
                with self.subTest(category=category,decision=decision):
                    r,q=self.review(category);r['decision']=decision;self.assertFalse(self.codes(self.run_check()));self.records.remove(r)
        r,q=self.review();r.pop('reviewType');r.pop('reviewerRole');self.assertFalse(self.codes(self.run_check()));self.assertEqual(self.report_row(q['id'])['reviews'][0]['vocabularySource'],'legacy-category-mapping')

    def test_field_scope_and_unresolved_issues_never_mean_whole_record_approval(self):
        r,q=self.review();self.appoint(r);r['scope']={'kind':'fields','fields':['/evaluation']};v=self.run_check();self.assertFalse(self.codes(v));self.assertFalse(v.approved(q,'scholarly'))
        r['scope']={'kind':'whole-record'};r['unresolvedIssues']=['Synthetic unresolved issue.'];v=self.run_check();self.assertFalse(v.approved(q,'scholarly'))

    def test_review_role_mismatch_and_invalid_timestamp_rejected(self):
        r,q=self.review();r['reviewerRole']='rights-reviewer';self.assertIn('SCHEMA',self.codes(self.run_check()));r['reviewerRole']='domain-reviewer';r['reviewedAt']='2026-11-06T10:00:00';self.assertIn('SCHEMA',self.codes(self.run_check()))

    def test_self_approval_and_declared_conflict_cannot_bypass_independence(self):
        r,q=self.review();r['reviewerRef']={'id':self.records[0]['id'],'revision':1};r['conflictsOfInterest']=[{'kind':'authorship','note':'Synthetic author review.','resolution':'requires-independent-review'}];self.assertIn('REVIEW-INDEPENDENCE',self.codes(self.run_check()))
        r['decision']='changes-requested';self.assertFalse(self.codes(self.run_check()))

    def test_latest_instant_and_tied_disagreement_do_not_use_lexical_order(self):
        r,q=self.review();self.appoint(r);later=copy.deepcopy(r);later.update(id=str(uuid.uuid4()),reviewedAt='2026-11-06T11:30:00+02:00',decision='rejected');self.records.append(later);v=self.run_check();self.assertTrue(v.approved(q,'scholarly')) # rejected 09:30Z predates approved 10:00Z
        later['reviewedAt']='2026-11-06T12:00:00+02:00';v=self.run_check();self.assertFalse(v.approved(q,'scholarly'))

    def test_private_fields_and_values_rejected_without_diagnostic_leak(self):
        # Reserved example.invalid address is synthetic negative-test input only.
        contact='synthetic-private'+'@'+'example.invalid'
        for field in ['email','phone','legalName']:
            with self.subTest(field=field):
                a=self.records[0];a[field]=contact;v=self.run_check();self.assertIn('SCHEMA',self.codes(v));self.assertNotIn(contact,str(v.issues));a.pop(field)
        self.records[0]['displayName']=contact;v=self.run_check();self.assertIn('IDENTITY-PRIVATE-VALUE',self.codes(v));self.assertNotIn(contact,str(v.issues));self.assertRaises(ValueError,working_report,self.root)

    def test_contact_in_review_and_attribution_notes_is_refused(self):
        r,q=self.review();r['rationale']='synthetic-private'+'@'+'example.invalid';self.assertIn('IDENTITY-PRIVATE-VALUE',self.codes(self.run_check()));r['rationale']='Synthetic review.';q['attributions'][0]['note']='mailto:synthetic-private'+'@'+'example.invalid';r['targetSha256']=digest(canonical(q));self.assertIn('IDENTITY-PRIVATE-VALUE',self.codes(self.run_check()))

    def test_public_identifier_validation_and_closed_agent_fields(self):
        a=self.records[0];a['externalIdentifiers']=[{'scheme':'github','value':'SyntheticPublicHandle'},{'scheme':'orcid','value':'0000-0000-0000-000X'}];self.assertFalse(self.codes(self.run_check()))
        a['externalIdentifiers'].append({'scheme':'github','value':'syntheticpublichandle'});self.assertIn('AGENT-IDENTIFIER-DUPLICATE',self.codes(self.run_check()));a['externalIdentifiers']=[{'scheme':'email','value':'invalid'}];self.assertIn('SCHEMA',self.codes(self.run_check()))
        a.pop('externalIdentifiers');a['displayName']='  ';self.assertIn('SCHEMA',self.codes(self.run_check()))

    def test_bad_public_links_are_rejected(self):
        for link in ['http://example.invalid/profile','https://example.invalid/profile?contact=hidden','https://user:pass@example.invalid/profile']:
            with self.subTest(link=link):self.records[0]['publicLinks']=[link];self.assertTrue(self.codes(self.run_check()))

    def test_submitter_differs_from_author_and_review(self):
        q=self.question();submitter=self.agent(name='Synthetic repository submitter');w=copy.deepcopy(self.records[0]);w.pop('displayName');w.pop('agentKind');w.update(id=str(uuid.uuid4()),entityType='workflow-record',targetRef={'id':q['id'],'revision':1},targetSha256=digest(canonical(q)),stage='draft',recordedAt='2026-11-06T10:00:00Z',note='Synthetic submission evidence only.',submission={'submitterRef':{'id':submitter['id'],'revision':1},'contextUri':'https://example.invalid/pull/1'});self.records.append(w)
        self.assertFalse(self.codes(self.run_check()));row=self.report_row(q['id']);self.assertNotEqual(row['attributions'][0]['agent']['id'],row['submissions'][0]['submitter']['id']);self.assertFalse(row['reviews'])

    def test_report_is_deterministic_without_git_api_or_contact_data(self):
        self.save()
        with patch('subprocess.run',side_effect=AssertionError('No Git/API needed for current records')),patch('subprocess.check_output',side_effect=AssertionError('No Git metadata read')):
            first=canonical(working_report(self.root));second=canonical(working_report(self.root));self.assertEqual(first,second);self.assertNotIn(b'@',first);self.assertNotIn(b'email',first)
        self.assertIn('| Authors |',markdown(json.loads(first)))

    def test_markdown_escapes_public_names(self):
        self.records[0]['displayName']='<script>synthetic | display</script>';self.save();output=markdown(working_report(self.root));self.assertNotIn('<script>',output);self.assertIn('&#124;',output)

    def synthetic_archive(self):
        # Deliberately not an eligible learner dataset: tests exact resolution only.
        q=next(r for r in self.records if r['entityType']=='collection')
        r,q=self.review('editorial',target=q);self.appoint(r)
        self.records=[x for x in self.records if x['entityType'] in ('agent','rights-statement','collection','review-record')]
        archive=self.root/'synthetic-archive';snapshot=archive/'snapshot';snapshot.mkdir(parents=True)
        for name in ['schemas','policies']:shutil.copytree(self.root/name,snapshot/name)
        m={'schemaVersion':'0.1.0','datasetVersion':'0.1.0-test.1','mode':'learner','baseGitCommit':'a'*40,'members':[],'resolutionMap':{},'files':[],'reviewDependencies':[],'assetDigests':[],'validation':{'errors':0,'validatorVersion':'0.1.0','mode':'release'},'attributionNotices':['Synthetic exact-resolution test only.'],'rightsNotices':['Unknown rights; no grants.'],'limitations':['Software fixture; not learner admission.'],'databaseRightsRef':{'id':self.records[1]['id'],'revision':1}}
        for p in sorted(snapshot.rglob('*.json')):m['files'].append({'path':str(p.relative_to(snapshot)),'sha256':digest(p.read_bytes())})
        for item in self.records:
            path=f'records/{item["id"]}/{item["revision"]}.json';p=archive/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canonical(item));m['members'].append({'id':item['id'],'revision':item['revision'],'entityType':item['entityType'],'path':path,'sha256':digest(p.read_bytes())});m['resolutionMap'][item['id']]=item['revision']
        (archive/'manifest.json').write_bytes(canonical(m));return archive,m,r,q

    def test_release_report_uses_pinned_offline_members_and_reviewer(self):
        archive,m,r,q=self.synthetic_archive()
        with patch('subprocess.run',side_effect=AssertionError('No Git or network')):
            report=release_report(archive);self.assertEqual(canonical(report),canonical(release_report(archive)))
        row=next(x for x in report['records'] if x['id']==q['id']);self.assertEqual(row['reviews'][0]['reviewer']['id'],r['reviewerRef']['id']);self.assertTrue(row['reviews'][0]['bindingValid']);self.assertTrue(row['independentApprovalByCategory']['editorial']);self.assertNotIn('email',canonical(report).decode())
        p=archive/m['members'][0]['path'];p.write_bytes(b'tampered');self.assertRaises(ValueError,release_report,archive)

    def test_release_report_refuses_private_notices_and_modified_policy(self):
        archive,m,r,q=self.synthetic_archive();m['rightsNotices']=['synthetic-private'+'@'+'example.invalid'];(archive/'manifest.json').write_bytes(canonical(m));self.assertRaises(ValueError,release_report,archive)
        m['rightsNotices']=[];(archive/'manifest.json').write_bytes(canonical(m));p=archive/'snapshot/policies/registry.json';s=load(p);s['reviewAuthorities']=[];p.write_bytes(canonical(s));self.assertRaises(ValueError,release_report,archive)

    def test_tooling_report_hash_and_recomputed_projection_are_verified(self):
        self.save();self.init_git();out=self.root.parent/(self.root.name+'-identity-release')
        try:
            m=archive_release(self.root,out,'0.1.0-test.2');self.assertEqual(m['attributionReport']['sha256'],digest((out/'attribution.json').read_bytes()));verify_release(out);self.assertEqual(load(out/'attribution.json')['records'],[])
            p=out/'attribution.json';x=load(p);x['notices']={};p.write_bytes(canonical(x));m['attributionReport']['sha256']=digest(p.read_bytes());(out/'manifest.json').write_bytes(canonical(m));self.assertRaises(ValueError,verify_release,out)
        finally:shutil.rmtree(out,ignore_errors=True)

    def test_agent_kind_uuid_missing_name_and_unknown_reference_rejected(self):
        a=self.records[0];old=a['agentKind'];a['agentKind']='account';self.assertIn('SCHEMA',self.codes(self.run_check()));a['agentKind']=old
        name=a.pop('displayName');self.assertIn('SCHEMA',self.codes(self.run_check()));a['displayName']=name
        self.question()['attributions'][0]['agentId']=str(uuid.uuid4());self.assertIn('REF-MISSING',self.codes(self.run_check()))

    def test_new_agent_uuid_must_be_v4_in_base_comparison(self):
        self.save();self.init_git();base=self.git_head();a=self.agent();a['id']=str(uuid.uuid5(uuid.NAMESPACE_DNS,'synthetic-identity.example.invalid'));self.save();self.assertIn('AGENT-UUID-NEW',self.codes(validate(self.root,base_commit=base)))

    def test_review_field_scope_must_exist_on_exact_target(self):
        r,q=self.review();r['scope']={'kind':'fields','fields':['/not-a-target-field']};self.assertIn('REVIEW-SCOPE',self.codes(self.run_check()))

    def test_report_rejects_contact_in_label_or_rights_notice(self):
        collection=next(r for r in self.records if r['entityType']=='collection');collection['title']='synthetic-private'+'@'+'example.invalid';self.save();self.assertRaises(ValueError,working_report,self.root)
        collection['title']='Synthetic collection';self.records[1]['obligations']=['synthetic-private'+'@'+'example.invalid'];self.save();self.assertRaises(ValueError,working_report,self.root)

    def test_release_reviewer_profile_remains_pinned_when_default_changes(self):
        archive,m,r,q=self.synthetic_archive();old=next(a for a in self.records if a['id']==r['reviewerRef']['id']);new={**old,'revision':2,'displayName':'Synthetic later public name'};path=f'records/{new["id"]}/2.json';p=archive/path;p.write_bytes(canonical(new));m['members'].append({'id':new['id'],'revision':2,'entityType':'agent','path':path,'sha256':digest(p.read_bytes())});m['resolutionMap'][new['id']]=2;(archive/'manifest.json').write_bytes(canonical(m))
        row=next(x for x in release_report(archive)['records'] if x['id']==q['id']);self.assertEqual(row['reviews'][0]['reviewer']['revision'],1);self.assertEqual(row['reviews'][0]['reviewer']['displayName'],old['displayName'])

    def test_real_metadata_and_registry_remain_unapproved(self):
        # Prior release files pin the original tooling schema/code; current data remain metadata only.
        config=load(ROOT/'policies/registry.json');self.assertEqual(config['reviewAuthorities'],[]);self.assertFalse(config['learnerReleaseEnabled'])
        report=working_report(ROOT);self.assertEqual(len(report['records']),4);self.assertTrue(all(r['authorshipStatus']=='not-recorded' and not r['reviews'] for r in report['records']))


if __name__=='__main__':unittest.main()
