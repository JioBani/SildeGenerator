"""Source-owned evidence references; selected IDs confer no quality approval."""
import re
from pydantic import Field
from .semantic_review import StrictModel


class EvidenceJudgment(StrictModel):
    beat_id: str
    evidence_id: str
    route_fit: str = Field(pattern='^(PASS|FAIL|UNKNOWN)$')
    grammar_fit: str = Field(pattern='^(PASS|FAIL|UNKNOWN)$')
    meaning_preserved: str = Field(pattern='^(PASS|FAIL|UNKNOWN)$')
    causality: str = Field(pattern='^(PASS|FAIL|UNKNOWN)$')
    information_sufficient: str = Field(pattern='^(PASS|FAIL|UNKNOWN)$')
    explanation: str = Field(min_length=1)
    repair_target: str | None
    recheck_scope: str | None


class EvidenceVerdict(StrictModel):
    beats: list[EvidenceJudgment] = Field(min_length=1,max_length=10)


def evidence_catalog(packet):
    result=[]
    for beat in packet['beats']:
        text=beat['literal_content']; number=0
        # These are evidence spans, not semantic beat boundaries. Long clauses
        # retain every character across bounded source slices.
        for match in re.finditer(r'.+?(?:[.!?](?=\s|$)|\Z)',text,re.S):
            for start in range(match.start(),match.end(),240):
                end=min(start+240,match.end())
                if not text[start:end].strip(): continue
                number+=1
                result.append(dict(id=f"{beat['beat_id']}-q{number:03d}",beat_id=beat['beat_id'],
                    start=start,end=end,text=text[start:end]))
    if not result: raise ValueError('semantic_evidence_empty')
    return result


def evidence_schema(packet):
    schema=EvidenceVerdict.model_json_schema()
    props=schema['$defs']['EvidenceJudgment']['properties']
    props['beat_id']['enum']=[b['beat_id'] for b in packet['beats']]
    props['evidence_id']['enum']=[q['id'] for q in evidence_catalog(packet)]
    return schema


def expand_evidence(raw,packet):
    wire=EvidenceVerdict.model_validate(raw)
    catalog={q['id']:q for q in evidence_catalog(packet)}
    result=[]
    for judgment in wire.beats:
        quote=catalog.get(judgment.evidence_id)
        if quote is None: raise ValueError('semantic_critic_evidence_id_unknown')
        if quote['beat_id']!=judgment.beat_id: raise ValueError('semantic_critic_evidence_beat_mismatch')
        item=judgment.model_dump(); item.pop('evidence_id')
        item['script_quote']=quote['text']
        result.append(item)
    return {'beats':result}
