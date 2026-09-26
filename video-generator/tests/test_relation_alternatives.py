import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from app.harness_sdk.semantic_beats import RelatedScriptAnalysis, analysis_sha256, relation_alternatives_extension, semantic_review_extension, RELATION_RULES
from app.relation_alternatives import relation_variants, resolve_relation_uncertainty
from app.semantic_gate import gate_context
from app.semantic_review import digest, exact_quote_options_for
from app.tracking import Tracker
from test_semantic_planning import analysis_payload, contract, SCRIPT
from test_semantic_gate import verdict_for, settings


def fixture():
    data = analysis_payload(); data['version'] = 'semantic-beats-0.2'
    for b in data['beats']: b.pop('cause_beat_numbers'); b['relations'] = []
    data['beats'][1]['relations'] = [dict(from_beat_number=1, kind='motivation', grounding='inferred',
        source_quote=data['beats'][0]['literal_content'], target_quote=data['beats'][1]['literal_content'], explanation='Uncertain connection')]
    analysis = RelatedScriptAnalysis.model_validate(data)
    active = contract('semantic-beats-0.2'); active['relation_alternatives'] = relation_alternatives_extension()
    active['semantic_review'] = semantic_review_extension()
    verdict = verdict_for(data)
    verdict['beats'][1].update(causality='UNKNOWN', repair_target='Consider a noncausal link', recheck_scope='One relation')
    report = dict(status='REVISE',response_id='fixture-review', analysis_sha256=analysis_sha256(analysis),
        script_sha256=hashlib.sha256(SCRIPT.encode()).hexdigest(), context_sha256=digest(gate_context(active)),
        relation_rules_sha256=digest(RELATION_RULES),model='gpt-5.6-terra',verdict=verdict)
    return analysis, active, report


class RelationAlternativeTests(unittest.TestCase):
    def test_strict_quote_enums_preserve_multiline_source_without_controls(self):
        source=' 첫 줄입니다.\n두 번째 줄\t마지막 줄.\n'
        values=exact_quote_options_for({'A':{'beats':[{'literal_content':source}]}})
        self.assertEqual(['첫 줄입니다.','두 번째 줄','마지막 줄.'],values)
        self.assertTrue(all(q in source and '\n' not in q and '\t' not in q for q in values))

    def test_only_kind_and_explanation_change(self):
        analysis, active, report = fixture()
        values = relation_variants(analysis,SCRIPT,report,active,'offline-generator')
        for kind,value in zip(['context','sequence'],values):
            baseline=analysis.model_dump(mode='json'); changed=value.model_dump(mode='json')
            baseline['beats'][1]['relations'][0]['kind']=kind
            baseline['beats'][1]['relations'][0]['explanation']=changed['beats'][1]['relations'][0]['explanation']
            self.assertEqual(baseline,changed)

    def test_explicit_or_multi_issue_cannot_be_downgraded(self):
        for mode in ('explicit','multiple','hash'):
            analysis,active,report=fixture()
            if mode=='explicit':
                analysis.beats[1].relations[0].grounding='explicit'
                report['analysis_sha256']=analysis_sha256(analysis)
            if mode=='multiple': report['verdict']['beats'][0].update(route_fit='FAIL',repair_target='Different issue',recheck_scope='Route')
            if mode=='hash':report['analysis_sha256']='changed'
            with self.assertRaises(ValueError):relation_variants(analysis,SCRIPT,report,active,'offline-generator')


class RelationAlternativeIntegration(unittest.IsolatedAsyncioTestCase):
    async def run_case(self,mode):
        analysis,active,report=fixture(); calls=[]
        def respond(request):
            body=json.loads(request.content);name=body['text']['format']['name'];calls.append(name)
            if mode=='401':return httpx.Response(401)
            if name=='independent_semantic_review':
                packet=json.loads(body['input'][0]['content'][0]['text'].split('\n',1)[1])
                candidates=[]
                for label,value in packet['candidates'].items():
                    entries=[]
                    for b in value['beats']:
                        entries.append(dict(beat_id=b['beat_id'],route_fit='PASS',grammar_fit='PASS',meaning_preserved='PASS',causality='PASS',
                            script_quote=b['literal_content'],explanation='Fixture checks preserved meaning',repair_target=None,recheck_scope=None))
                    candidates.append(dict(label=label,beats=entries))
                preferred=next(label for label,value in packet['candidates'].items() if value['beats'][1]['relations'][0]['kind']=='context')
                if mode=='disagree' and len(calls)==2:preferred='A'
                raw=dict(candidates=candidates,preferred=preferred,reason='Retains context without adding causality')
            else:
                raw=verdict_for(analysis.model_dump(mode='json'))
                if mode=='final_fail':raw['beats'][1].update(causality='FAIL',repair_target='Not preserved',recheck_scope='Relation')
            return httpx.Response(200,text='event: response.completed\ndata: '+json.dumps({'type':'response.completed','response':{
                'id':f'fixture-{len(calls)}','status':'completed','usage':{},'output':[{'content':[{'type':'output_text','text':json.dumps(raw)}]}]}})+'\n\n')
        client=httpx.AsyncClient
        with tempfile.TemporaryDirectory() as temp:
            work=Path(temp);tracker=Tracker(work)
            with patch('app.planner.httpx.AsyncClient',side_effect=lambda **kw:client(transport=httpx.MockTransport(respond),**kw)):
                if mode in {'disagree','401','final_fail','budget'}:
                    with self.assertRaises((RuntimeError,ValueError)):
                        await resolve_relation_uncertainty(analysis,SCRIPT,report,active,settings(),tracker,work,
                            attempt=2 if mode=='budget' else 1,generator_model='offline-generator')
                else:
                    selected,attempt=await resolve_relation_uncertainty(analysis,SCRIPT,report,active,settings(),tracker,work,
                        attempt=1,generator_model='offline-generator')
                    self.assertEqual(3,attempt);self.assertEqual('context',selected.beats[1].relations[0].kind)
                    self.assertEqual(['independent_semantic_review']*2+['semantic_sufficiency'],calls)
            if mode=='budget':self.assertEqual([],calls)
            if mode=='disagree':self.assertEqual(2,len(calls))

    async def test_bounded_counterbalanced_recovery(self):await self.run_case('pass')
    async def test_disagreement_stops(self):await self.run_case('disagree')
    async def test_final_check_cannot_be_skipped(self):await self.run_case('final_fail')
    async def test_provider_failure_no_fallback(self):await self.run_case('401')
    async def test_shared_budget(self):await self.run_case('budget')


if __name__=='__main__':unittest.main()
