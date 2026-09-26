import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.harness_sdk.semantic_beats import ScriptAnalysis, semantic_review_extension
from app.harness_sdk.preproduction import preproduction_extension
from app.semantic_gate import (SufficiencyVerdict, DIMENSIONS, verdict_findings, require_acceptance,
                               review_sufficiency, acceptance_valid)
from app.semantic_review import review_packet
from app.semantic_planning import analyze_script
from app.planner import create_plan, plan_with_codex
from app.prompts import load_prompts
from app.tracking import Tracker
from test_semantic_planning import contract, analysis_payload, proposal, SCRIPT, ROOT


def verdict_for(analysis, status="PASS"):
    result = []
    for i, beat in enumerate(analysis["beats"], 1):
        result.append(dict(beat_id=f"beat-{i:03d}", **{k: status for k in DIMENSIONS},
            script_quote=beat["literal_content"], explanation="Literal content supports the requested relation" if status == "PASS" else "Explanation has no operands",
            repair_target=None if status == "PASS" else "Regroup the related clauses without changing script",
            recheck_scope=None if status == "PASS" else "Meaning beats"))
    return {"beats": result}


def active_contract(evidence_ids=False):
    value = contract()
    value["semantic_review"] = semantic_review_extension(evidence_ids=evidence_ids)
    return value


def settings():
    return SimpleNamespace(runner_mode="live", schemas_dir=ROOT / "video-generator/schemas", codex_model="offline-generator",
        codex_reasoning_effort="low", codex_fast_mode=False, codex_read_timeout_seconds=10,
        codex_connect_timeout_seconds=2, subscription_base_url="http://offline.invalid")


def initial_bad_analysis():
    value = analysis_payload()
    value["beats"] = value["beats"][:1]
    value["beats"][0]["literal_content"] = SCRIPT
    return value


class SufficiencyContractTests(unittest.TestCase):
    def test_validated_quotes_complete_coverage_and_repair_evidence(self):
        packet = review_packet(ScriptAnalysis.model_validate(analysis_payload()))
        passing = verdict_for(analysis_payload())
        self.assertEqual(([], []), verdict_findings(SufficiencyVerdict.model_validate(passing), packet))
        for mutation in ("quote", "coverage", "repair"):
            value = deepcopy(passing)
            if mutation == "quote": value["beats"][0]["script_quote"] = "not a script quote"
            if mutation == "coverage": value["beats"].reverse()
            if mutation == "repair": value["beats"][0]["information_sufficient"] = "FAIL"
            with self.assertRaises(ValueError): verdict_findings(SufficiencyVerdict.model_validate(value), packet)

    def test_missing_acceptance_does_not_grant_permission(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "must_precede"):
                require_acceptance(Path(folder), ScriptAnalysis.model_validate(analysis_payload()), SCRIPT, active_contract(), "offline-generator")
            require_acceptance(Path(folder), None, SCRIPT, contract(), "offline-generator")


class SufficiencyIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, mode):
        calls, stages, analysis_count = [], [], 0
        active=active_contract(evidence_ids=mode.startswith('referenced'))
        if mode == 'preproduction':
            active['preproduction_brief'] = preproduction_extension()
        current = None
        def respond(request):
            nonlocal analysis_count, current
            body = json.loads(request.content)
            calls.append(body)
            name = body["text"]["format"]["name"]
            stages.append(name)
            if name == "semantic_beats":
                analysis_count += 1
                current = initial_bad_analysis() if mode in {"repair", "unchanged", "repeated"} and (analysis_count == 1 or mode == "unchanged") else analysis_payload()
                value = current
            elif name == "semantic_sufficiency":
                self.assertEqual("gpt-5.6-terra", body["model"])
                self.assertNotIn('"confidence":', body["input"][0]["content"][0]["text"])
                if mode == "401": return httpx.Response(401, json={"error": "offline"})
                status = "UNKNOWN" if mode == "unknown" else "FAIL" if (mode in {"repair", "unchanged"} and analysis_count == 1) or mode == "repeated" else "PASS"
                value = verdict_for(current, status)
                if mode.startswith('referenced'):
                    from app.semantic_evidence import evidence_catalog
                    packet=review_packet(ScriptAnalysis.model_validate(current))
                    catalog=evidence_catalog(packet)
                    self.assertIn('EvidenceJudgment',body['text']['format']['schema']['$defs'])
                    for item in value['beats']:
                        item.pop('script_quote')
                        item['evidence_id']=next(q['id'] for q in catalog if q['beat_id']==item['beat_id'])
                    if mode=='referenced_cross_beat':
                        value['beats'][0]['evidence_id']=value['beats'][1]['evidence_id']
                if mode == "bad_quote": value["beats"][0]["script_quote"] = "invented"
                if mode == "runaway": value["beats"][0]["explanation"] = "x" * 8001
            else:
                self.assertEqual("scene_plan", name)
                value = proposal()
            response = dict(type="response.completed", response=dict(id=f"offline-{len(calls)}", status="completed", usage={},
                output=[dict(content=[dict(type="output_text", text=json.dumps(value))])]))
            return httpx.Response(200, text="event: response.completed\ndata: " + json.dumps(response) + "\n\n")
        client = httpx.AsyncClient
        prompts, _ = load_prompts(ROOT / "harnesses/hybrid-story/prompts")
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            tracker = Tracker(work)
            with patch("app.planner.httpx.AsyncClient", side_effect=lambda **kw: client(transport=httpx.MockTransport(respond), **kw)):
                if mode in {"401", "unknown", "bad_quote", "unchanged", "repeated", "runaway", "referenced_cross_beat"}:
                    with self.assertRaises((RuntimeError, ValueError)):
                        await create_plan(SCRIPT, prompts, settings(), tracker, work, harness_planning_contract=active)
                    self.assertNotIn("scene_plan", stages)
                else:
                    plan = await create_plan(SCRIPT, prompts, settings(), tracker, work, harness_planning_contract=active)
                    self.assertEqual(SCRIPT, ''.join(s.narration for s in plan.scenes))
                    self.assertTrue(all(s.layout["semantic_sufficiency"]["prepared_by"] == "core_semantic_gate" for s in plan.scenes))
                    self.assertEqual(["semantic_beats", "semantic_sufficiency"] * (2 if mode == "repair" else 1) + ["scene_plan"], stages)
                    accepted = json.loads(sorted(work.glob("semantic-sufficiency-*.json"))[-1].read_text())
                    analysis = ScriptAnalysis.model_validate(analysis_payload())
                    require_acceptance(work, analysis, SCRIPT, active, settings().codex_model)
                    for field in ("analysis_sha256", "script_sha256", "context_sha256", "model", "response_id"):
                        altered = deepcopy(accepted); altered[field] = ""
                        self.assertFalse(acceptance_valid(altered, analysis, SCRIPT, active, settings().codex_model))
                    altered = deepcopy(accepted)
                    altered["verdict"]["beats"][0]["information_sufficient"] = "FAIL"
                    self.assertFalse(acceptance_valid(altered, analysis, SCRIPT, active, settings().codex_model))
                    if mode=='referenced':
                        for field in ('wire_verdict','evidence_catalog_sha256'):
                            altered=deepcopy(accepted); altered.pop(field)
                            self.assertFalse(acceptance_valid(altered,analysis,SCRIPT,active,settings().codex_model))
                        self.assertFalse(acceptance_valid(accepted,analysis,SCRIPT,active_contract(),settings().codex_model))
                    if mode == 'preproduction':
                        brief_path = work / 'preproduction-brief.json'
                        brief = json.loads(brief_path.read_text(encoding='utf-8'))
                        self.assertEqual(['cinematic_still','editable_diagram'],
                            [b['execution']['route'] for b in brief['beats']])
                        self.assertIn('runtime/preproduction-brief.json',calls[-1]['input'][0]['content'][0]['text'])
                        brief['analysis_sha256'] = 'tampered'
                        brief_path.write_text(json.dumps(brief),encoding='utf-8')
                        with self.assertRaisesRegex(ValueError,'preproduction_brief_changed_during_repair'):
                            await plan_with_codex(SCRIPT,prompts,settings(),tracker,work,
                                harness_planning_contract=active,semantic_analysis_result=analysis)
            if mode == "unchanged": self.assertEqual(["semantic_beats", "semantic_sufficiency", "semantic_beats"], stages)
            if mode == "repeated": self.assertEqual(["semantic_beats", "semantic_sufficiency"] * 2, stages)
            if mode in {"401", "unknown", "bad_quote", "runaway"}: self.assertEqual(["semantic_beats", "semantic_sufficiency"], stages)
            self.assertFalse(any(u["stage"] in {"image_generation", "voice_generation"} for u in tracker.usage))

    async def test_review_precedes_scene_design(self): await self.run_case("ok")
    async def test_preproduction_brief_is_used_and_hash_bound_in_real_core_path(self): await self.run_case('preproduction')
    async def test_repair_rechecks_changed_plan_with_shared_budget(self): await self.run_case("repair")
    async def test_repeated_failure_stops(self): await self.run_case("repeated")
    async def test_unchanged_plan_cannot_retry_the_critic(self): await self.run_case("unchanged")
    async def test_unknown_needs_alternatives_not_confidence_inflation(self): await self.run_case("unknown")
    async def test_critic_401_has_no_fallback(self): await self.run_case("401")
    async def test_fabricated_critic_quote_cannot_approve(self): await self.run_case("bad_quote")
    async def test_runaway_critic_cannot_approve_or_retry(self): await self.run_case("runaway")
    async def test_referenced_evidence_in_real_core_path(self): await self.run_case('referenced')
    async def test_referenced_wrong_beat_blocks_assets(self): await self.run_case('referenced_cross_beat')

    async def test_direct_scene_entry_cannot_bypass_review(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            prompts, _ = load_prompts(ROOT / "harnesses/hybrid-story/prompts")
            with self.assertRaisesRegex(ValueError, "must_precede"):
                await plan_with_codex(SCRIPT,prompts,settings(),Tracker(work),work,
                    harness_planning_contract=active_contract(),semantic_analysis_result=ScriptAnalysis.model_validate(analysis_payload()))
