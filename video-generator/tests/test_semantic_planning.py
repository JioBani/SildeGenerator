import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from pydantic import ValidationError
from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.semantic_beats import ScriptAnalysis, inspect_analysis, bind_and_check_beats, semantic_planning_extension, semantic_enabled
from app.harness_sdk.direction import direction_planning_extension
from app.harness_sdk.hybrid import hybrid_planning_extension
from app.semantic_planning import analysis_schema, analysis_units
from app.planner import create_plan, compile_source_units
from app.prompts import load_prompts
from app.tracking import Tracker
from test_hybrid_story import route
from test_narrative_direction import shot
from test_planner import semantic_proposal

ROOT=Path(__file__).resolve().parents[2]
PARTS=["미나는 어두운 길 앞에서 망설였지만 ","전등을 켜자 길이 밝아졌다."]
SCRIPT=''.join(PARTS)


def analysis_payload(parts=PARTS):
    beats=[]
    for i,(literal,purpose,route_id) in enumerate(zip(parts,["feel","understand"],["cinematic","diagram"])):
        beats.append(dict(literal_content=literal,story_function="Experience hesitation" if i==0 else "Explain the visible change",
            information_function="Observe the obstacle" if i==0 else "A switch enables illumination",
            viewer_state_before="Unsure what happens",viewer_state_after="Sees the obstacle" if i==0 else "Understands the change",
            primary_purpose=purpose,route=route_id,route_reason="Experience a person's hesitation" if i==0 else "Make the switch and illumination relationship visible",
            rejected_routes=[dict(route=r,reason="This beat has a different primary purpose") for r in ("cinematic","diagram","source") if r!=route_id],
            new_information=literal.strip(),emotional_change="Hesitation" if i==0 else None,cause_beat_numbers=[] if i==0 else [1],
            research_need="none",required_evidence=[],grammar=None if i==0 else "cause_change_result",
            transition_to_next="Move from obstacle to its explanation" if i==0 else "End on the stated result",confidence=.9))
    return dict(version="semantic-beats-0.1",script_type="mixed",central_idea="A hesitant traveller and an illuminated path",beats=beats)


def contract(version="semantic-beats-0.1", film=False):
    loaded=HarnessRegistry(ROOT/"harnesses").load("hybrid-story")
    value=loaded.instance.describe_planning_contract(loaded.config)
    value.pop("concept_selection", None)
    value.pop("locked_scene_design", None)
    value.pop("semantic_review", None)
    value.pop("visible_text_review", None)
    value.pop("relation_alternatives", None)
    value.pop("preproduction_brief", None)
    value["semantic_analysis"]=semantic_planning_extension(version)
    value["hybrid_direction"]=hybrid_planning_extension("hybrid-scene-0.4" if film else "hybrid-scene-0.1")
    value["narrative_direction"]=direction_planning_extension("narrative-direction-0.2" if version.endswith("0.2") else "narrative-direction-0.1")
    return value


def proposal():
    value=semantic_proposal()
    value["continuity_assets"]=[]
    items=value["sequences"][0]["scene_groups"][0]["scenes"]
    for i,item in enumerate(items):
        item["layout"]["direction"]=shot(subject_id=f"subject-{i}",new_information=f"Information {i}")
        item["layout"]["hybrid"]=route("cinematic" if i==0 else "diagram")
    diagram=items[1]["layout"]["hybrid"]["diagram"]
    diagram["title"]="전등을 켜면 길이 보입니다"
    for node,label in zip(diagram["nodes"],["스위치","조명","길"]): node["label"]=label
    return value


class MeaningContractTests(unittest.TestCase):
    def test_missing_capability_reporting_is_explicit_and_backward_compatible(self):
        old = semantic_planning_extension("semantic-beats-0.2")
        new = semantic_planning_extension("semantic-beats-0.2", report_missing=True)
        self.assertNotIn("capability_reporting", old)
        self.assertEqual("required-grammar-0.1", new["capability_reporting"])
        self.assertTrue(semantic_enabled({"semantic_analysis": old}))
        self.assertTrue(semantic_enabled({"semantic_analysis": new}))
        new["capability_reporting"] = "skip-validation"
        with self.assertRaisesRegex(ValueError, "unsupported"):
            semantic_enabled({"semantic_analysis": new})

    def test_numeric_context_cannot_be_stranded_in_its_own_diagram(self):
        from app.harness_sdk.semantic_beats import RelatedScriptAnalysis
        for text,valid in [('This is a fictional example.',False),('If no water is lost, ',False),
                           ('The total is 45 liters.',False),('10 liters plus 20 liters plus 15 liters, with no loss, totals 45 liters.',True)]:
            data=analysis_payload([PARTS[0],text]); data['version']='semantic-beats-0.2'
            for beat in data['beats']:
                beat.pop('cause_beat_numbers'); beat['relations']=[]
            data['beats'][1]['grammar']='cumulative_change'
            findings=inspect_analysis(RelatedScriptAnalysis.model_validate(data),PARTS[0]+text,contract('semantic-beats-0.2',film=True))
            issue='beat-002:numeric_grammar_needs_two_items_keep_connected_context'
            self.assertEqual(not valid,issue in findings)

    def test_mid_sentence_beats_preserve_every_character(self):
        analysis=ScriptAnalysis.model_validate(analysis_payload())
        self.assertEqual(1,len(compile_source_units(SCRIPT)))
        units=analysis_units(analysis)
        self.assertEqual(2,len(units))
        self.assertEqual(SCRIPT,''.join(u.text for u in units))
        for unit in units: self.assertEqual(unit.text,SCRIPT[unit.start_offset:unit.end_offset])
        self.assertEqual([],inspect_analysis(analysis,SCRIPT,contract()))

    def test_loss_and_order_are_not_silently_repaired(self):
        data=analysis_payload()
        data["beats"][0]["literal_content"]=data["beats"][0]["literal_content"].strip()
        self.assertIn("semantic_source_coverage_not_exact",inspect_analysis(ScriptAnalysis.model_validate(data),SCRIPT,contract()))
        data=analysis_payload()
        data["beats"][0]["cause_beat_numbers"]=[2]
        self.assertIn("beat-001:cause_not_earlier",inspect_analysis(ScriptAnalysis.model_validate(data),SCRIPT,contract()))

    def test_wrong_route_and_missing_alternatives_fail(self):
        for change in (dict(route="diagram"),dict(rejected_routes=[]),dict(viewer_state_after="Unsure what happens")):
            data=analysis_payload()
            data["beats"][0].update(change)
            with self.assertRaises(ValidationError): ScriptAnalysis.model_validate(data)

    def test_unavailable_grammar_and_uncertainty_need_work(self):
        data=analysis_payload()
        data["beats"][1].update(grammar="whole_detail",confidence=.6)
        findings=inspect_analysis(ScriptAnalysis.model_validate(data),SCRIPT,contract())
        self.assertIn("beat-002:grammar_not_supported",findings)
        self.assertIn("beat-002:independent_route_comparison_required",findings)

    def test_source_claim_is_exact_and_registry_is_required(self):
        data=analysis_payload()
        beat=data["beats"][1]
        beat.update(primary_purpose="verify",route="source",grammar=None,
            rejected_routes=[dict(route=r,reason="Direct source verification required") for r in ("cinematic","diagram")],
            required_evidence=[dict(claim_quote=beat["literal_content"],source_id="not-registered",acceptance_criteria=["Shows precisely the stated claim"])])
        self.assertIn("beat-002:SOURCE_NOT_AVAILABLE",inspect_analysis(ScriptAnalysis.model_validate(data),SCRIPT,contract()))
        beat["required_evidence"][0]["claim_quote"]="Invented claim"
        with self.assertRaises(ValidationError): ScriptAnalysis.model_validate(data)

    def test_structured_output_schema_has_no_optional_properties(self):
        def walk(value):
            if isinstance(value,dict):
                if value.get("type")=="object":
                    self.assertEqual(False,value["additionalProperties"])
                    self.assertEqual(set(value["properties"]),set(value["required"]))
                if "const" in value: self.assertIn("type",value)
                for item in value.values(): walk(item)
            elif isinstance(value,list):
                for item in value: walk(item)
        walk(analysis_schema())

    def test_scene_binding_is_core_owned_and_does_not_silently_switch(self):
        analysis=ScriptAnalysis.model_validate(analysis_payload())
        scenes=[SimpleNamespace(id=f"scene-{i:03d}",source_unit_ids=[f"unit-{i:03d}"],narration=b.literal_content,
            layout={"semantic_beat":{"route":"forged"},"hybrid":{"route":b.route,"diagram":{"grammar":b.grammar}}}) for i,b in enumerate(analysis.beats,1)]
        self.assertEqual([],bind_and_check_beats(scenes,analysis))
        self.assertEqual("feel",scenes[0].layout["semantic_beat"]["primary_purpose"])
        scenes[1].layout["hybrid"]["route"]="cinematic"
        self.assertIn("scene-002:semantic_route_changed",bind_and_check_beats(scenes,analysis))
        scenes[0].source_unit_ids=["unit-001","unit-002"]
        self.assertIn("scene-001:semantic_beat_merge_or_missing",bind_and_check_beats(scenes,analysis))


class MeaningPlannerIntegration(unittest.IsolatedAsyncioTestCase):
    async def run_case(self,mode):
        requests=[]
        prompts,_=load_prompts(ROOT/"harnesses/hybrid-story/prompts")
        plan_requests=0
        analysis_requests=0
        def respond(request):
            nonlocal plan_requests, analysis_requests
            body=json.loads(request.content);requests.append(body)
            if mode=="provider_error": return httpx.Response(401,json={"error":"offline test"})
            name=body["text"]["format"]["name"]
            if name=="semantic_beats":
                analysis_requests+=1
                output=analysis_payload()
                if mode in {"typed_relations", "film_design", "film_design_repair"}:
                    output["version"]="semantic-beats-0.2"
                    for b in output["beats"]:
                        b.pop("cause_beat_numbers")
                        b["relations"]=[]
                    output["beats"][1]["relations"]=[dict(from_beat_number=1,kind="context",source_quote=PARTS[0].strip(),
                        target_quote=PARTS[1],grounding="explicit",explanation="Hesitation establishes the context, not the cause of illumination.")]
                if mode=="lost_text": output["beats"][0]["literal_content"]="미나는 "
                if mode=="shared_budget" and analysis_requests==1: output["beats"][0]["literal_content"]="미나는 "
                if mode=="unsupported": output["beats"][1]["grammar"]="whole_detail"
                if mode=="uncertain": output["beats"][0]["confidence"]=.6
            else:
                plan_requests+=1
                output=proposal()
                if mode in {"typed_relations", "film_design", "film_design_repair"}:
                    for s in output["sequences"][0]["scene_groups"][0]["scenes"]:
                        s["layout"]["direction"]["version"]="narrative-direction-0.2"
                        if mode.startswith("film_design"):
                            from test_film_design import design
                            hybrid=s["layout"]["hybrid"]
                            hybrid.update(version="hybrid-scene-0.4",design=design())
                            if hybrid["diagram"]:
                                for i,n in enumerate(hybrid["diagram"]["nodes"]):
                                    n["color"]=design()["palette"]["accents"][i]
                                if mode=="film_design_repair" and plan_requests==1:
                                    hybrid["design"]["typography"]["title_px"]=36
                if mode=="runaway":
                    output["sequences"][0]["scene_groups"][0]["scenes"][0]["motion"][0]["phases"]=["Hold still. Read the result. End the scene. "*200]
                if mode in {"route_exhaust", "changing_failure_set"} or (mode in {"route_repair","shared_budget"} and plan_requests==1):
                    output["sequences"][0]["scene_groups"][0]["scenes"][1]["layout"]["hybrid"]=route("cinematic")
                if mode=="changing_failure_set" and plan_requests==2:
                    output["sequences"][0]["scene_groups"][0]["scenes"][0]["layout"]["direction"]["cause_scene_number"]=99
                if mode=="shared_budget" and plan_requests==2:
                    # A different error can consume the remaining shared budget;
                    # a repeated grammar failure must stop instead.
                    output["sequences"][0]["scene_groups"][0]["scenes"][0]["layout"]["direction"]["cause_scene_number"]=99
            response={"type":"response.completed","response":{"id":"mock-only","status":"completed","usage":{},
                "output":[{"content":[{"type":"output_text","text":json.dumps(output,ensure_ascii=False)}]}]}}
            return httpx.Response(200,text="event: response.completed\ndata: "+json.dumps(response)+"\n\n")
        settings=SimpleNamespace(runner_mode="live",schemas_dir=ROOT/"video-generator/schemas",codex_model="mock-only",
            codex_reasoning_effort="low",codex_fast_mode=False,codex_read_timeout_seconds=10,codex_connect_timeout_seconds=2,subscription_base_url="http://offline.invalid")
        original=httpx.AsyncClient
        with tempfile.TemporaryDirectory() as directory:
            work=Path(directory); tracker=Tracker(work)
            with patch("app.planner.httpx.AsyncClient",side_effect=lambda **kw:original(transport=httpx.MockTransport(respond),**kw)):
                if mode in {"lost_text","route_exhaust","changing_failure_set","provider_error","unsupported","uncertain","runaway"}:
                    with self.assertRaises(RuntimeError):
                        await create_plan(SCRIPT,prompts,settings,tracker,work,harness_id="hybrid-story",harness_planning_contract=contract())
                else:
                    active=contract("semantic-beats-0.2" if mode in {"typed_relations","film_design","film_design_repair"} else "semantic-beats-0.1",film=mode.startswith("film_design"))
                    plan=await create_plan(SCRIPT,prompts,settings,tracker,work,harness_id="hybrid-story",harness_planning_contract=active)
                    if mode.startswith("film_design"):
                        from app.harness_sdk.film_design import shared_design
                        self.assertEqual("night-route-editorial",shared_design(plan.scenes).concept_id)
                        if mode=="film_design_repair":
                            self.assertIn("film_design_invalid_or_inconsistent",json.dumps(requests[-1]))
                    if mode=="typed_relations":
                        self.assertEqual("context",plan.scenes[1].layout["semantic_beat"]["relations"][0]["kind"])
                        self.assertNotIn("cause_beat_numbers",plan.scenes[1].layout["semantic_beat"])
                    self.assertEqual(PARTS,[s.narration for s in plan.scenes])
                    self.assertEqual(["cinematic","diagram"],[s.layout["hybrid"]["route"] for s in plan.scenes])
                    self.assertEqual(2,len(plan.source_units))
                    self.assertTrue((work/"semantic-analysis-0.json").is_file())
                    self.assertIn("accepted-meaning-analysis",json.dumps(requests[-1]))
                    self.assertIsNone(json.loads((work/"semantic-analysis-0.json").read_text())["human_approval"])
            self.assertEqual("semantic_beats",requests[0]["text"]["format"]["name"])
            expected={"ok":2,"route_repair":3,"route_exhaust":3,"changing_failure_set":3,"lost_text":2,"provider_error":1,"unsupported":1,"uncertain":1,"shared_budget":5,"runaway":2,"typed_relations":2,"film_design":2,"film_design_repair":3}[mode]
            self.assertEqual(expected,len(requests))
            if mode=="changing_failure_set":
                stopped=json.loads((work/"planning-stop.repair-1.json").read_text())
                self.assertEqual("ENGINE_WORK_REQUIRED",stopped["status"])
                self.assertTrue(stopped["repeated_causes"])
                self.assertFalse((work/"director-repair-request-2.json").exists())
            self.assertTrue(any(a.get("stage")=="semantic_analysis" for a in tracker.usage))
            self.assertFalse(any(a.get("stage") in {"image_generation","voice_generation"} for a in tracker.usage))

    async def test_analysis_precedes_scene_design(self): await self.run_case("ok")
    async def test_typed_relations_survive_real_planning_path(self): await self.run_case("typed_relations")
    async def test_shared_design_survives_real_planning_path(self): await self.run_case("film_design")
    async def test_design_drift_is_repaired_before_assets(self): await self.run_case("film_design_repair")
    async def test_route_substitution_is_repaired(self): await self.run_case("route_repair")
    async def test_repeated_route_failure_stops(self): await self.run_case("route_exhaust")
    async def test_repeated_failure_stops_when_another_error_is_added(self): await self.run_case("changing_failure_set")
    async def test_source_loss_stops_before_design(self): await self.run_case("lost_text")
    async def test_401_never_falls_back(self): await self.run_case("provider_error")
    async def test_unsupported_grammar_is_not_reinterpreted(self): await self.run_case("unsupported")
    async def test_uncertainty_cannot_be_retried_as_fake_confidence(self): await self.run_case("uncertain")
    async def test_analysis_and_design_share_three_repairs(self): await self.run_case("shared_budget")
    async def test_runaway_completion_does_not_retry_or_create_assets(self): await self.run_case("runaway")

    async def test_plain_mock_mode_is_not_claimed_as_semantic_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,"no deterministic fallback"):
                await create_plan(SCRIPT,{},SimpleNamespace(runner_mode="mock"),Tracker(Path(directory)),Path(directory),harness_planning_contract=contract())
