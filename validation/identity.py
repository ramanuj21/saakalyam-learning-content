"""Public identity/credit and review rules. Never reads Git account metadata."""
from __future__ import annotations
import datetime
import hashlib
import json
import re
from urllib.parse import urlsplit

ATTRIBUTION_ROLES = (
    'author', 'contributor', 'translator', 'transcriber', 'editor',
    'commentator', 'annotator', 'curator', 'reviewer', 'adapter',
    'creator', 'narrator', 'producer',
)
REVIEW_TYPES = {
    'scholarly': ('sanskrit-domain', 'domain-reviewer'),
    'source-fidelity': ('source-fidelity', 'source-reviewer'),
    'pedagogical': ('pedagogical', 'pedagogical-reviewer'),
    'editorial': ('editorial', 'editorial-reviewer'),
    'rights': ('rights', 'rights-reviewer'),
    'technical': ('technical-schema', 'technical-reviewer'),
}
EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}")
PRIVATE_FIELDS = {'email','emailaddress','privateemail','phone','telephone','mobile','postaladdress','address','legalname','governmentid','dateofbirth','privatecontact','employer'}
COMMON_FIELDS = {'id','entityType','schemaVersion','revision','origin','attributions','rightsId','ownership','provenance'}
AGENT_FIELDS = COMMON_FIELDS | {'agentKind','displayName','externalIdentifiers','publicLinks'}


def values(value, path=''):
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from values(item, path+'/'+str(key).replace('~','~0').replace('/','~1'))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from values(item, path+'/'+str(index))


def privacy_issues(record):
    """Conservative public-identity checks; return paths/codes, never private values."""
    if not isinstance(record, dict):
        return []
    kind = record.get('entityType')
    targets = [('', record)] if kind in ('agent','review-record','workflow-record') else [('/attributions',record.get('attributions',[])),('/provenance/attributionCorrection',record.get('provenance',{}).get('attributionCorrection',{}))]
    problems = []
    for prefix, target in targets:
        for path, value in values(target, prefix):
            key = path.rsplit('/',1)[-1].replace('-','').replace('_','').lower()
            if key in PRIVATE_FIELDS:
                problems.append((path,'IDENTITY-PRIVATE-FIELD','Private contact/legal-identity fields do not belong in public identity or editorial metadata.'))
            if isinstance(value,str) and (EMAIL.search(value) or value.lower().startswith(('mailto:','tel:'))):
                problems.append((path,'IDENTITY-PRIVATE-VALUE','Contact information must not enter public identities, editorial notes or generated attribution.'))
    if kind == 'agent':
        display = record.get('displayName','')
        if isinstance(display,str) and re.fullmatch(r'\+?\d[\d(). -]{6,}\d',display):
            problems.append(('/displayName','IDENTITY-PRIVATE-VALUE','A contact number is not a public display name.'))
    return problems


def assert_public_text(value):
    for _, item in values(value):
        if isinstance(item,str) and (EMAIL.search(item) or item.lower().startswith(('mailto:','tel:'))):
            raise ValueError('Attribution output refused: public contact information found; no private value is included in this diagnostic.')


def public_agent(record):
    if not record or record.get('entityType') != 'agent':
        raise ValueError('Attribution requires an exact, resolvable Agent record.')
    if set(record)-AGENT_FIELDS or privacy_issues(record):
        raise ValueError('Attribution output refused: unsafe public Agent metadata.')
    result = {key:record[key] for key in ('id','revision','agentKind','displayName')}
    for key in ('externalIdentifiers','publicLinks'):
        if record.get(key):
            result[key] = record[key]
    assert_public_text(result)
    return result


def validate_public_identifiers(record):
    issues = []
    seen = set()
    for index, item in enumerate(record.get('externalIdentifiers',[])):
        scheme, value = item['scheme'], item['value']
        key = (scheme,value.casefold())
        if key in seen:
            issues.append(('/externalIdentifiers/'+str(index),'AGENT-IDENTIFIER-DUPLICATE','The same public identifier is repeated.'))
        seen.add(key)
        valid = (scheme=='github' and re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?',value)) or (scheme=='orcid' and re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]',value))
        if not valid:
            issues.append(('/externalIdentifiers/'+str(index),'AGENT-IDENTIFIER','Use a public GitHub handle or hyphenated ORCID identifier; no contact identifiers.'))
    for index, link in enumerate(record.get('publicLinks',[])):
        uri = urlsplit(link)
        if uri.scheme!='https' or not uri.netloc or uri.username or uri.password or uri.query:
            issues.append(('/publicLinks/'+str(index),'AGENT-PUBLIC-LINK','Public profile links must be stable HTTPS references without credentials or query parameters.'))
    return issues


def attribution_issues(record):
    problems, seen = [], set()
    for index, attribution in enumerate(record.get('attributions',[])):
        key = (attribution.get('agentId'),attribution['role'])
        if key in seen:
            problems.append(('/attributions/'+str(index),'ATTRIBUTION-DUPLICATE','A role/Agent pair, or an unknown role, must not be duplicated by changing its note or scope.'))
        seen.add(key)
    return problems


def review_description(review):
    expected = REVIEW_TYPES[review['reviewScope']]
    return {
        'reviewType':review.get('reviewType',expected[0]),
        'reviewerRole':review.get('reviewerRole',expected[1]),
        'scope':review.get('scope',{'kind':'whole-record'}),
        'vocabularySource':'explicit' if 'reviewType' in review and 'reviewerRole' in review else 'legacy-category-mapping',
    }


def review_binding(review, target, raw, critical_refs):
    problems = []
    if not target or review['targetRef'] != {'id':target['id'],'revision':target['revision']}:
        return ['target-revision-unresolved']
    if hashlib.sha256(raw).hexdigest()!=review['targetSha256']:
        problems.append('target-digest-mismatch')
    expected = {json.dumps(ref,sort_keys=True) for ref in critical_refs}
    supplied = {json.dumps(ref,sort_keys=True) for ref in review['dependencyRefs']}
    if not expected.issubset(supplied):
        problems.append('critical-dependencies-missing')
    description = review_description(review)
    if (description['reviewType'],description['reviewerRole']) != REVIEW_TYPES[review['reviewScope']]:
        problems.append('review-role-type-mismatch')
    for pointer in description['scope'].get('fields',[]):
        value=target
        try:
            for token in pointer.split('/')[1:]:
                token=token.replace('~1','/').replace('~0','~')
                if isinstance(value,list):
                    if not re.fullmatch(r'0|[1-9][0-9]*',token):raise KeyError(token)
                    value=value[int(token)]
                else:value=value[token]
        except (KeyError,IndexError,TypeError,ValueError):problems.append('scope-field-unresolved')
    return problems


def independent(review, target):
    # A legacy reviewer credit does not turn the scholar into the content author.
    creators = {a['agentId'] for a in target['attributions'] if a.get('agentId') and a['role']!='reviewer'}
    return review['reviewerRef']['id'] not in creators and not review.get('conflictsOfInterest')


def appointed(review, authorities):
    return any(a.get('agentId')==review['reviewerRef']['id'] and review['reviewScope'] in a.get('scopes',[]) for a in authorities)


def reviewed_instant(review):
    return datetime.datetime.fromisoformat(review['reviewedAt'].upper().replace('Z','+00:00')).astimezone(datetime.timezone.utc)


def approved_for_record(target, scope, reviews, authorities, raw_for, critical_refs):
    candidates = []
    for review in reviews:
        if review['reviewScope']!=scope or review['targetRef']!={'id':target['id'],'revision':target['revision']}:
            continue
        if review_binding(review,target,raw_for(target),critical_refs) or not independent(review,target) or not appointed(review,authorities):
            continue
        candidates.append(review)
    if not candidates:
        return False
    latest = max(reviewed_instant(r) for r in candidates)
    final = [r for r in candidates if reviewed_instant(r)==latest]
    # Tied disagreement is pending; UUID sorting must never decide scholarly truth.
    return all(r['decision']=='approved' and not r.get('unresolvedIssues') and review_description(r)['scope']['kind']=='whole-record' for r in final)
