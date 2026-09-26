import unittest
from copy import deepcopy
from pydantic import ValidationError
from app.semantic_evidence import evidence_catalog,evidence_schema,expand_evidence
from app.semantic_gate import SufficiencyVerdict,verdict_findings


class SemanticEvidenceTests(unittest.TestCase):
    def packet(self):
        return {'beats':[{'beat_id':'beat-001','literal_content':'Value is 1.5 cm. Do not infer a cause.\n'},
            {'beat_id':'beat-002','literal_content':'\"Quoted text\" is present. 한글 문장입니다.'}]}

    def verdict(self,packet):
        return {'beats':[dict(beat_id=b['beat_id'],evidence_id=next(q['id'] for q in evidence_catalog(packet) if q['beat_id']==b['beat_id']),
            **{key:'PASS' for key in ('route_fit','grammar_fit','meaning_preserved','causality','information_sufficient')},
            explanation='Independent fixture judgment, not film approval',repair_target=None,recheck_scope=None) for b in packet['beats']]}

    def test_exact_offsets_decimal_quotations_and_korean(self):
        packet=self.packet(); catalog=evidence_catalog(packet)
        self.assertIn('1.5 cm.',catalog[0]['text'])
        for quote in catalog:
            source=next(b['literal_content'] for b in packet['beats'] if b['beat_id']==quote['beat_id'])
            self.assertEqual(source[quote['start']:quote['end']],quote['text'])
        expanded=expand_evidence(self.verdict(packet),packet)
        self.assertEqual(([],[]),verdict_findings(SufficiencyVerdict.model_validate(expanded),packet))
        self.assertEqual('"Quoted text" is present.',expanded['beats'][1]['script_quote'])

    def test_long_text_bounded_and_not_lost(self):
        text='A'*20000
        packet={'beats':[dict(beat_id='beat-001',literal_content=text)]}
        catalog=evidence_catalog(packet)
        self.assertEqual(text,''.join(q['text'] for q in catalog))
        self.assertLessEqual(max(len(q['text']) for q in catalog),240)
        self.assertEqual(len(catalog),len({q['id'] for q in catalog}))

    def test_unknown_wrong_beat_and_injected_extra_fields_rejected(self):
        packet=self.packet()
        for kind in ('unknown','wrong_beat','extra'):
            raw=self.verdict(packet)
            if kind=='unknown': raw['beats'][0]['evidence_id']='invented'
            if kind=='wrong_beat': raw['beats'][0]['evidence_id']=raw['beats'][1]['evidence_id']
            if kind=='extra': raw['beats'][0]['script_quote']='forged source'
            with self.assertRaises(ValueError): expand_evidence(raw,packet)
        raw=self.verdict(packet); raw['beats'].reverse()
        with self.assertRaisesRegex(ValueError,'coverage'):
            verdict_findings(SufficiencyVerdict.model_validate(expand_evidence(raw,packet)),packet)

    def test_schema_is_strict_and_ids_not_approval(self):
        packet=self.packet(); schema=evidence_schema(packet)
        fields=schema['$defs']['EvidenceJudgment']
        self.assertNotIn('script_quote',fields['properties'])
        self.assertEqual(set(fields['required']),set(fields['properties']))
        self.assertFalse(fields['additionalProperties'])
        self.assertEqual([q['id'] for q in evidence_catalog(packet)],fields['properties']['evidence_id']['enum'])
        raw=self.verdict(packet); raw['beats'][0].update(information_sufficient='UNKNOWN',repair_target='Need operand',recheck_scope='beat-001')
        findings,_=verdict_findings(SufficiencyVerdict.model_validate(expand_evidence(raw,packet)),packet)
        self.assertEqual(['beat-001:semantic_review:information_sufficient'],findings)


if __name__=='__main__': unittest.main()
