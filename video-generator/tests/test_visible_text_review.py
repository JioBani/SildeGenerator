import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from app.harness_sdk.visible_text import visible_text_extension
from app.visible_text_review import text_packet, verdict_findings, apply_text_repairs, ensure_visible_text, select_text_alternatives
from app.semantic_review import digest
from app.plan_compiler import compile_scene_plan
from app.planner import create_plan
from app.semantic_planning import analysis_units
from app.harness_sdk.semantic_beats import ScriptAnalysis
from app.prompts import load_prompts
from app.tracking import Tracker
from test_semantic_planning import contract, proposal, SCRIPT, ROOT, analysis_payload
from test_semantic_gate import settings


def plan_fixture():
    units = analysis_units(ScriptAnalysis.model_validate(analysis_payload()))
    return compile_scene_plan(proposal(), SCRIPT, units, continuity_enabled=False)[0]


def verdict(packet, status='PASS'):
    return {'texts': [dict(text_id=t['text_id'], completeness=status if i == 0 else 'PASS',
        fidelity='PASS', referent_clarity='PASS', explanation='Offline fixture judgment',
        repair_target='Write a complete concise heading' if i == 0 and status != 'PASS' else None)
        for i, t in enumerate(packet['texts'])]}


class VisibleTextUnitTests(unittest.TestCase):
    def test_alternatives_are_filtered_never_truncated(self):
        packet = text_packet(plan_fixture())
        report = dict(packet_sha256=digest(packet), verdict=verdict(packet, 'FAIL'))
        selected = select_text_alternatives(packet, report, {'text-001': ['x'*60, '빛과 변화', '전등과 길의 변화']})
        self.assertEqual({'text-001': '빛과 변화'}, selected)
        for values in [['same']*3, ['x'*60, 'y'*60, 'z'*60], ['one', 'two']]:
            with self.assertRaises(ValueError): select_text_alternatives(packet, report, {'text-001': values})

    def test_exact_coverage_and_failure_evidence(self):
        packet = text_packet(plan_fixture())
        good = verdict(packet)
        self.assertEqual([], verdict_findings(good, packet)[1])
        for kind in ('missing', 'reordered', 'repair_missing', 'unknown_id'):
            bad = deepcopy(good)
            if kind == 'missing': bad['texts'].pop()
            if kind == 'reordered': bad['texts'].reverse()
            if kind == 'repair_missing': bad['texts'][0]['fidelity'] = 'FAIL'
            if kind == 'unknown_id': bad['texts'][0]['text_id'] = 'other'
            with self.assertRaises(ValueError): verdict_findings(bad, packet)

    def test_repair_cannot_edit_narration_quantities_or_successful_text(self):
        plan = plan_fixture(); packet = text_packet(plan)
        report = dict(packet_sha256=digest(packet), verdict=verdict(packet, 'FAIL'))
        changed = apply_text_repairs(plan, packet, report, {'text-001': '전등과 길의 변화'}, contract())
        before = plan.model_dump(mode='json'); after = changed.model_dump(mode='json')
        before['scenes'][1]['layout']['hybrid']['diagram']['title'] = '전등과 길의 변화'
        self.assertEqual(before, after)
        for edits in ({'narration': 'replace'}, {'text-001': 'ok', 'text-002': 'not requested'},
                      {'text-001': 'x'*49}, {'text-001': packet['texts'][0]['text']}):
            with self.assertRaises(ValueError): apply_text_repairs(plan, packet, report, edits, contract())
        packet['texts'][0]['text'] = 'mutated'
        with self.assertRaises(ValueError): apply_text_repairs(plan, packet, report, {'text-001': 'ok'}, contract())


class VisibleTextPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, mode):
        active = contract(); active['visible_text_review'] = visible_text_extension()
        plan = plan_fixture(); packet = text_packet(plan); names = []; reviews = 0
        def respond(request):
            nonlocal reviews
            body = json.loads(request.content); name = body['text']['format']['name']; names.append(name)
            if name == 'semantic_beats': raw = analysis_payload()
            elif name == 'scene_plan': raw = proposal()
            elif name.startswith('visible-text-repair'):
                raw = {'text-001': ['전등과 길의 변화', '전등을 켜면 밝아지는 길', '조명으로 밝아진 길의 모습']}
                if mode == 'scope': raw['narration'] = 'replace'
            else:
                reviews += 1
                self.assertEqual('gpt-5.6-terra', body['model'])
                if mode == '401': return httpx.Response(401)
                status = 'UNKNOWN' if mode == 'unknown' else 'FAIL' if mode in {'repair', 'repeat', 'scope', 'no_budget'} and (reviews == 1 or mode == 'repeat') else 'PASS'
                raw = verdict(packet, status)
            return httpx.Response(200, text='event: response.completed\ndata: '+json.dumps({'type':'response.completed',
                'response':{'id':f'fixture-{len(names)}','status':'completed','usage':{},'output':[{'content':[{'type':'output_text','text':json.dumps(raw)}]}]}})+'\n\n')
        client = httpx.AsyncClient
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder); tracker = Tracker(work)
            with patch('app.planner.httpx.AsyncClient', side_effect=lambda **kw: client(transport=httpx.MockTransport(respond), **kw)):
                if mode == 'legacy':
                    result = await ensure_visible_text(plan, contract(), settings(), tracker, work, generator_model='offline-generator', repair_budget=1, attempt=0)
                    self.assertIs(result, plan); self.assertEqual([], names)
                    return
                if mode in {'unknown', '401', 'scope', 'repeat', 'no_budget'}:
                    with self.assertRaises((ValueError, RuntimeError)):
                        await ensure_visible_text(plan, active, settings(), tracker, work, generator_model='offline-generator',
                            repair_budget=0 if mode == 'no_budget' else 1, attempt=0)
                else:
                    prompts, _ = load_prompts(ROOT/'harnesses/hybrid-story/prompts')
                    result = await create_plan(SCRIPT, prompts, settings(), tracker, work, harness_planning_contract=active)
                    self.assertEqual(SCRIPT, ''.join(s.narration for s in result.scenes))
                    self.assertEqual('VISIBLE_TEXT_PASS', result.scenes[1].layout['visible_text_review']['status'])
                    if mode == 'repair': self.assertEqual('전등과 길의 변화', result.scenes[1].layout['hybrid']['diagram']['title'])
            self.assertLessEqual(reviews, 2)
            if mode in {'unknown', '401', 'no_budget'}: self.assertEqual(1, len(names))
            self.assertFalse(any(u['stage'] in {'image_generation', 'voice_generation'} for u in tracker.usage))

    async def test_actual_core_entry_reviews_output(self): await self.run_case('pass')
    async def test_actual_core_repairs_only_text_then_rechecks(self): await self.run_case('repair')
    async def test_unknown_stops(self): await self.run_case('unknown')
    async def test_provider_error_no_fallback(self): await self.run_case('401')
    async def test_scope_override_rejected(self): await self.run_case('scope')
    async def test_repeated_failure_stops(self): await self.run_case('repeat')
    async def test_no_shared_budget_left(self): await self.run_case('no_budget')
    async def test_legacy_has_no_added_calls(self): await self.run_case('legacy')


if __name__ == '__main__': unittest.main()
