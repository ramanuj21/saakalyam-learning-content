"""Deterministic offline public attribution; no GitHub API or Git identity reads."""
from pathlib import Path
from .core import canonical, digest, load, references, validate, Validator
from .identity import (ATTRIBUTION_ROLES, assert_public_text, public_agent,
    privacy_issues, validate_public_identifiers, attribution_issues, review_description,
    review_binding, independent, appointed, approved_for_record)

CONTENT_TYPES={'question','rubric','scholarly-component','collection','resource','media-asset'}
FORMAT='saakalyam-attribution-v1'


def project(records, resolve, raw_for, authorities, source, notices=None):
    """Project exact records only. References and schema are checked by the adapter."""
    all_records=sorted(records,key=lambda r:(r['id'],r['revision']))
    reviews=[r for r in all_records if r['entityType']=='review-record']
    workflows=[r for r in all_records if r['entityType']=='workflow-record' and r.get('submission')]
    rows=[]
    for r in all_records:
        if r['entityType'] not in CONTENT_TYPES:continue
        credits=[]
        for a in r['attributions']:
            credit={k:a[k] for k in ('role','attributionStatus','note','scope','evidenceRefs') if k in a}
            if a.get('agentId'):credit['agent']=public_agent(resolve({'id':a['agentId']}))
            else:credit['agent']=None
            credits.append(credit)
        credits.sort(key=lambda a:(a['role'],a['agent']['id'] if a['agent'] else '',canonical(a)))
        row={
            'id':r['id'],'revision':r['revision'],'entityType':r['entityType'],
            'label':r.get('title',r.get('fileName',r['entityType'].replace('-',' ').title()+' '+r['id'])),
            'sha256':digest(raw_for(r)),'attributions':credits,
            'authorshipStatus':'recorded' if any(a['role']=='author' for a in credits) else 'not-recorded',
            'provenance':r['provenance'],'origin':r['origin'],
            'reviews':[],'submissions':[],'rights':[],
        }
        if 'sourceCreditLine' in r:row['sourceCreditLine']=r['sourceCreditLine']
        for category,key in [('record','rightsId'),('reproduction','reproductionRightsId')]:
            if key not in r:continue
            rights=resolve({'id':r[key]})
            row['rights'].append({'category':category,'rightsHolders':[public_agent(resolve(ref)) for ref in rights.get('rightsHolderRefs',[])],**{k:rights[k] for k in ('id','revision','basis','licenseExpression','obligations','proposedUses','conditions','unresolvedQuestions') if k in rights}})
        for review in reviews:
            if review['targetRef']['id']!=r['id']:continue
            target=resolve(review['targetRef']);valid=not review_binding(review,target,raw_for(target),[v for _,v,_ in references(target) if 'revision' in v])
            row['reviews'].append({
                'id':review['id'],'revision':review['revision'],'targetRef':review['targetRef'],
                'targetSha256':review['targetSha256'],'reviewer':public_agent(resolve(review['reviewerRef'])),
                'category':review['reviewScope'],**review_description(review),
                **{k:review[k] for k in ('decision','reviewedAt','rationale','dependencyRefs','evidenceRefs','limitations','unresolvedIssues','conflictsOfInterest') if k in review},
                'bindingValid':valid,'appliesToDisplayedRevision':valid and review['targetRef']['revision']==r['revision'],
                'independent':independent(review,target),'appointedForCategory':appointed(review,authorities),
            })
        for workflow in workflows:
            if workflow['targetRef']['id']==r['id']:
                s=workflow['submission']
                row['submissions'].append({'workflowRef':{'id':workflow['id'],'revision':workflow['revision']},'targetRef':workflow['targetRef'],'submitter':public_agent(resolve(s['submitterRef'])),**{k:s[k] for k in ('contextUri','commitSha') if k in s}})
        row['independentApprovalByCategory']={scope:approved_for_record(r,scope,reviews,authorities,raw_for,[v for _,v,_ in references(r) if 'revision' in v]) for scope in ('scholarly','source-fidelity','pedagogical','editorial','rights','technical')}
        rows.append(row)
    report={'format':FORMAT,'source':source,'records':rows,'notices':notices or {},'limitations':[
        'Structured public credit only. Omitted authorship is not inferred; an explicit unknown credit has no Agent.',
        'Recorded reviews apply only to exact target bytes and declared scope. Approval categories do not substitute for one another.',
        'Attribution, source credit, repository submission and review do not grant rights or establish learner-release eligibility.',
    ]}
    assert_public_text(report)
    return report


def working_report(root):
    v=validate(root)
    if any(d.severity=='error' for d in v.issues):raise ValueError('Attribution output refused: authoring validation has errors; inspect safe diagnostics first.')
    def resolve(ref):
        r=v.resolve(ref,historical=True)
        if not r:raise ValueError('Attribution reference unavailable at exact revision.')
        return r
    return project(v.records.values(),resolve,v.raw_for,v.config.get('reviewAuthorities',[]),{'kind':'working-tree'})


def release_report(archive, manifest=None, schema_root=None):
    """Only the archived resolution map/members are authority; never current main."""
    from .resolution import ReleaseResolver
    archive=Path(archive).resolve();m=manifest if manifest is not None else load(archive/'manifest.json')
    if schema_root is None:
        snapshot=(archive/'snapshot').resolve();seen=set()
        for entry in m['files']:
            p=snapshot/entry['path']
            if entry['path'] in seen or p.is_symlink() or not p.resolve().is_relative_to(snapshot) or not p.is_file() or digest(p.read_bytes())!=entry['sha256']:raise ValueError('Pinned release schema/policy file missing, duplicated or altered.')
            seen.add(entry['path'])
        required={'policies/registry.json'}|{str(p.relative_to(snapshot)) for p in (snapshot/'schemas').rglob('*.json')}
        if not required.issubset(seen):raise ValueError('Release schemas/policy must be hash-pinned in the manifest.')
    resolver=ReleaseResolver(archive,m)
    v=Validator(schema_root or archive/'snapshot');v.setup();v.shape(m,'manifest','manifest.json')
    for r in resolver.members.values():
        if not v.shape(r,r['entityType'],'archived-record'):continue
        if privacy_issues(r) or attribution_issues(r):raise ValueError('Unsafe or duplicated attribution metadata in release.')
        if r['entityType']=='agent' and validate_public_identifiers(r):raise ValueError('Unsafe public Agent identifier in release.')
    if any(d.severity=='error' for d in v.issues):raise ValueError('Pinned archive schema validation failed.')
    # Default sidecars may target historical members; do not revive superseded sidecar revisions.
    selected=[r for key,r in resolver.members.items() if resolver.defaults.get(key[0])==key[1]]
    def raw_for(r):return (archive/f'records/{r["id"]}/{r["revision"]}.json').read_bytes()
    return project(selected,resolver.resolve,raw_for,v.config.get('reviewAuthorities',[]),{'kind':'release','datasetVersion':m['datasetVersion'],'baseGitCommit':m['baseGitCommit']},{k:m.get(k,[]) for k in ('attributionNotices','rightsNotices')})


def markdown(report):
    assert_public_text(report)
    def escape(value):
        import html
        return html.escape(str(value),quote=True).replace('|','&#124;').replace('\r',' ').replace('\n','<br>')
    def credits(row,roles):
        return '; '.join(escape(a['agent']['displayName'] if a['agent'] else 'Unknown')+' ('+escape(a['role'])+((', '+escape(a['attributionStatus'])) if 'attributionStatus' in a else '')+')'+((': '+escape(a['note'])) if 'note' in a else '') for a in row['attributions'] if a['role'] in roles) or 'Not recorded'
    lines=['# Public attribution report','', 'Source: '+escape(report['source']['kind'])+'. This report does not confer publication or rights approval.','', '| Content / revision | Authors | Contributors | Translators | Editors | Other credit | Reviews | Rights |','| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in report['records']:
        reviewed='; '.join(escape(x['reviewer']['displayName'])+' — '+escape(x['reviewType'])+': '+escape(x['decision'])+' ('+escape(x['scope']['kind'])+'; '+('current' if x['appliesToDisplayedRevision'] else 'historical')+'; '+('appointed' if x['appointedForCategory'] else 'unappointed')+')' for x in r['reviews']) or 'None recorded'
        rights='; '.join(escape(x['category'])+': '+escape(x['basis'])+(('; '+escape('; '.join(x.get('obligations',[])))) if x.get('obligations') else '') for x in r['rights'])
        lines.append('| '+' | '.join([escape(r['label'])+'<br>'+r['id']+' @ '+str(r['revision']),credits(r,{'author'}),credits(r,{'contributor','adapter'}),credits(r,{'translator'}),credits(r,{'editor'}),credits(r,set(ATTRIBUTION_ROLES)-{'author','contributor','adapter','translator','editor'}),reviewed,rights])+' |')
    lines+=['','The JSON report retains full role qualification, source credit, exact digests, provenance, reviewer limitations, rights obligations and separate submitter evidence. Preserve it with downstream exports.','']
    for notice in report.get('notices',{}).values():lines.extend(escape(n) for n in notice)
    return '\n'.join(lines).rstrip()+'\n'
