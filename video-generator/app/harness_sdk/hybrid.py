"""Public, provider-free scene routing contract for hybrid films."""
from __future__ import annotations

from copy import deepcopy
from typing import Annotated, Literal
from pydantic import Field, ValidationError, model_validator
from .direction import DirectionModel
from .film_design import FilmDesignContract, shared_design
from .snapshot_pair import SnapshotPair
from .spatial_map import SpatialMap


SHORT = Annotated[str, Field(min_length=1, max_length=48)]
ID = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]


class DiagramNode(DirectionModel):
    id: ID
    label: SHORT
    before: SHORT
    after: SHORT
    x: float = Field(ge=.12, le=.88)
    y: float = Field(ge=.2, le=.65)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    reveal_at: float = Field(ge=0, le=.65)
    change_at: float = Field(ge=.1, le=.85)
    quantity: float | None = Field(ge=0, le=1e12)
    unit: SHORT | None
    source_quote: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def ordered(self):
        if self.change_at < self.reveal_at + .05:
            raise ValueError("state_change_must_follow_reveal")
        return self


class DiagramEdge(DirectionModel):
    source: ID
    target: ID
    label: SHORT
    start_at: float = Field(ge=.05, le=.7)
    end_at: float = Field(ge=.1, le=.85)


class Diagram(DirectionModel):
    title: SHORT
    grammar: Literal["cause_change_result", "quantitative_comparison", "transport_track", "cumulative_change", "step_sequence", "before_after", "map_spatial"]
    nodes: list[DiagramNode] = Field(max_length=6)
    edges: list[DiagramEdge] = Field(max_length=8)
    comparison_scale_max: float | None = Field(gt=0, le=1e12)
    snapshot_pair: SnapshotPair | None = None
    spatial_map: SpatialMap | None = None

    @model_validator(mode="after")
    def coherent(self):
        if self.grammar == 'map_spatial':
            if len(self.title)>26 or self.spatial_map is None or self.nodes or self.edges or self.snapshot_pair is not None or self.comparison_scale_max is not None:
                raise ValueError('map_spatial_requires_exclusive_spatial_contract')
            return self
        if self.spatial_map is not None:
            raise ValueError('spatial_payload_requires_map_grammar')
        if self.grammar == 'before_after':
            if len(self.title)>26:
                raise ValueError('before_after_title_exceeds_single_line_budget')
            if self.snapshot_pair is None or self.nodes or self.edges or self.comparison_scale_max is not None:
                raise ValueError('before_after_requires_pair_without_nodes_edges_or_duplicate_scale')
            return self
        if self.snapshot_pair is not None or len(self.nodes)<2:
            raise ValueError('node_grammar_requires_nodes_without_snapshot_pair')
        nodes = {node.id: node for node in self.nodes}
        if len(nodes) != len(self.nodes):
            raise ValueError("duplicate_diagram_node")
        for edge in self.edges:
            if edge.source not in nodes or edge.target not in nodes or edge.source == edge.target:
                raise ValueError("invalid_diagram_edge")
            if edge.end_at <= edge.start_at or edge.start_at < max(nodes[edge.source].reveal_at, nodes[edge.target].reveal_at):
                raise ValueError("edge_must_follow_visible_nodes")
            if self.grammar == "cause_change_result" and nodes[edge.target].change_at < edge.end_at:
                raise ValueError("effect_precedes_cause_arrival")
        for i, node in enumerate(self.nodes):
            if any(abs(node.x - other.x) < .22 and abs(node.y - other.y) < .18 for other in self.nodes[i + 1:]):
                raise ValueError("diagram_nodes_overlap")
        if self.grammar == "quantitative_comparison":
            if self.comparison_scale_max is None or any(n.quantity is None or not n.unit for n in self.nodes):
                raise ValueError("comparison_requires_quantities_units_and_common_scale")
            if len({n.unit for n in self.nodes}) != 1 or any(n.quantity > self.comparison_scale_max for n in self.nodes):
                raise ValueError("comparison_scale_or_units_mismatch")
        elif self.grammar == "cumulative_change":
            if self.edges or self.comparison_scale_max is None or any(n.quantity is None or not n.unit for n in self.nodes):
                raise ValueError("accumulation_requires_increments_units_and_scale_without_edges")
            if len({n.unit for n in self.nodes}) != 1 or sum(n.quantity for n in self.nodes) > self.comparison_scale_max:
                raise ValueError("accumulation_scale_or_units_mismatch")
            if any(b.change_at <= a.change_at or b.x <= a.x for a,b in zip(self.nodes,self.nodes[1:])):
                raise ValueError("accumulation_events_out_of_order")
        elif self.grammar == "step_sequence":
            if len(self.edges) != len(self.nodes)-1 or self.comparison_scale_max is not None or any(n.quantity is not None or n.unit is not None for n in self.nodes):
                raise ValueError("steps_require_ordered_chain_not_quantities")
            for a,b,edge in zip(self.nodes,self.nodes[1:],self.edges):
                if (edge.source,edge.target)!=(a.id,b.id) or b.change_at-a.change_at < .15 or a.change_at > edge.start_at or edge.end_at > b.change_at:
                    raise ValueError("step_chain_or_timing_invalid")
        elif not self.edges:
            raise ValueError("relational_grammar_requires_edges")
        return self


class MapPoint(DirectionModel):
    x: float = Field(ge=.1, le=.9)
    y: float = Field(ge=.25, le=.68)


class IllustratedTransport(DirectionModel):
    version: Literal["illustrated-transport-0.1"]
    asset_pack_id: ID
    # Four cubic controls, in the uncropped plate's normalized coordinates.
    points: list[MapPoint] = Field(min_length=4, max_length=4)
    subject_width: float = Field(ge=.06, le=.16)
    start_at: float = Field(ge=.1, le=.3)
    end_at: float = Field(ge=.5, le=.8)
    route_color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")

    @model_validator(mode="after")
    def continuous_path(self):
        from math import hypot
        if self.end_at - self.start_at < .3:
            raise ValueError("transport_motion_too_short")
        if any(hypot(a.x - b.x, a.y - b.y) < .025 for a, b in zip(self.points, self.points[1:])):
            raise ValueError("transport_degenerate_tangent")
        # Restrict this first capability to monotonic paths; loops and abrupt U-turns
        # need a different path/heading contract, not ambiguous spline fitting.
        dx = [b.x - a.x for a, b in zip(self.points, self.points[1:])]
        if not (all(d > .01 for d in dx) or all(d < -.01 for d in dx)):
            raise ValueError("transport_nonmonotonic_path")
        return self


class HybridScene(DirectionModel):
    version: Literal["hybrid-scene-0.1", "hybrid-scene-0.2", "hybrid-scene-0.3", "hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"]
    route: Literal["cinematic", "diagram", "source"]
    reason: str = Field(min_length=12, max_length=800)
    diagram: Diagram | None
    source_id: ID | None
    composition: IllustratedTransport | None = None
    design: FilmDesignContract | None = None

    @model_validator(mode="after")
    def exclusive(self):
        if self.design is not None and self.design.version in {'film-design-0.2', 'film-design-0.3'} and self.version != 'hybrid-scene-0.6':
            raise ValueError('graphic_design_requires_scene_version_06')
        if (self.version in {"hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"}) != (self.design is not None):
            raise ValueError("film_design_requires_scene_version_04")
        if self.design is not None and self.diagram is not None:
            accents = {c.lower() for c in self.design.palette.accents}
            if any(n.color.lower() not in accents for n in self.diagram.nodes):
                raise ValueError("diagram_color_outside_film_palette")
            if self.diagram.snapshot_pair and self.diagram.snapshot_pair.color.lower() not in accents:
                raise ValueError('diagram_color_outside_film_palette')
            if self.diagram.spatial_map and any(p.color.lower() not in accents for p in self.diagram.spatial_map.places):
                raise ValueError('diagram_color_outside_film_palette')
        if self.design is not None and self.composition is not None:
            if self.composition.route_color.lower() not in {c.lower() for c in self.design.palette.accents}:
                raise ValueError("transport_color_outside_film_palette")
        if (self.diagram is not None) != (self.route == "diagram"):
            raise ValueError("diagram_route_payload_mismatch")
        if (self.source_id is not None) != (self.route == "source"):
            raise ValueError("source_route_payload_mismatch")
        if self.diagram is not None:
            if self.diagram.grammar == 'map_spatial' and self.version != 'hybrid-scene-0.6':
                raise ValueError('map_spatial_requires_scene_version_06')
            if self.diagram.grammar == 'before_after' and self.version not in {'hybrid-scene-0.5','hybrid-scene-0.6'}:
                raise ValueError('before_after_requires_scene_version_05')
            if self.version not in {"hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"} and self.diagram.grammar == "cumulative_change":
                if any(b.change_at-a.change_at < .12 for a,b in zip(self.diagram.nodes,self.diagram.nodes[1:])):
                    raise ValueError("accumulation_events_out_of_order")
            if self.diagram.grammar in {"cumulative_change", "step_sequence"} and self.version not in {"hybrid-scene-0.3", "hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"}:
                raise ValueError("grammar_requires_scene_version_03")
            if self.version in {"hybrid-scene-0.3", "hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"} and self.diagram.grammar in {"quantitative_comparison", "cumulative_change", "step_sequence"}:
                if len(self.diagram.nodes) > 4:
                    raise ValueError("semantic_diagram_max_four_items")
                if any(len(n.label) > 14 or len(n.after) > 20 for n in self.diagram.nodes):
                    raise ValueError("semantic_diagram_label_too_long")
                if self.diagram.grammar != "step_sequence" and any(not n.source_quote for n in self.diagram.nodes):
                    raise ValueError("quantity_requires_source_quote")
                if self.diagram.grammar == "quantitative_comparison" and self.diagram.edges:
                    raise ValueError("comparison_does_not_imply_causal_edges")
                if self.diagram.grammar != "step_sequence" and any(len(f"{n.quantity:g} {n.unit}") > 9 for n in self.diagram.nodes):
                    raise ValueError("quantity_label_requires_shorter_unit_or_scale")
        if self.composition is not None:
            if self.version not in {"hybrid-scene-0.2", "hybrid-scene-0.3", "hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"} or self.route != "diagram" or self.diagram.grammar != "transport_track":
                raise ValueError("illustrated_transport_route_version_mismatch")
            if len(self.diagram.nodes) != 2 or len(self.diagram.edges) != 1:
                raise ValueError("illustrated_transport_requires_two_endpoints")
            edge = self.diagram.edges[0]
            nodes = {n.id: n for n in self.diagram.nodes}
            for node, point in [(nodes[edge.source], self.composition.points[0]), (nodes[edge.target], self.composition.points[-1])]:
                if abs(node.x - point.x) > .0001 or abs(node.y - point.y) > .0001:
                    raise ValueError("transport_endpoint_mismatch")
            if abs(edge.start_at - self.composition.start_at) > .0001 or abs(edge.end_at - self.composition.end_at) > .0001:
                raise ValueError("transport_timeline_mismatch")
            if nodes[edge.target].change_at < self.composition.end_at:
                raise ValueError("transport_arrival_state_precedes_arrival")
        return self


def hybrid_planning_extension(version="hybrid-scene-0.1"):
    if version == 'hybrid-scene-0.6':
        result=hybrid_planning_extension('hybrid-scene-0.5')
        result['version']=version
        result['grammars'].append('map_spatial')
        # The growing library must fit the existing bounded planning packet.
        # Keep legacy contracts byte-for-byte stable; only v0.6 uses this summary.
        result['rules']=[
            'Every scene has layout.hybrid. Route by purpose: cinematic stills for experience, editable diagrams for relations, registered sources for evidence. Preserve narration order; hard cuts only; no fallback.',
            'Source IDs and illustration packs come only from trusted catalogs. Preserve date and meaning limits; modern images cannot prove historical events. Missing evidence is not generated art.',
            'Only cinematic routes generate images and use bounded push/pull. Diagram/source cameras hold. Coordinates and times are normalized; keep labels concise and final reading hold >=15%.',
            'Comparison uses 2-4 same-unit values on one zero baseline; accumulation uses 2-4 ordered nonnegative increments with computed totals. Each numeric source_quote is literal narration with value and unit. No invented numbers or causal edges.',
            'step_sequence is a stated linear procedure, 2-4 nodes and ordered chain, not unordered categories, branching or causality. cause_change_result needs actual cause and changed target, visible in that order.',
            'Optional illustrated-transport-0.1: registered matching art, exactly two endpoints and one edge, four monotonic cubic controls inside safe_rect with sprite clearance. Match node/path endpoints and timing; no articulated acting or obstacle avoidance.',
            'Copy one film-design-0.1 across routes. Node/path accents belong to palette; text contrast >=4.5 on background and surface, accents/lines >=3 on background. No baked diagram text or edited source pixels.',
            'before_after: one named entity/metric/unit, two ordered quoted numeric snapshots, common zero scale in snapshot_pair. Nodes/edges empty; no intermediate data or causal inference.',
        ]
        result['rules'].append('map_spatial: relative north-up schematic, never surveyed geography. 2-6 named places, 0-2 disjoint rectangular regions; north/south/east/west and inside/outside relations with exact ordered quotes naming both referents. No distances, travel, arrows, boundary shapes or invented landmarks. Fixed coordinates, reveal then highlight; unsupported actual maps require registered evidence.')
        return result
    if version == 'hybrid-scene-0.5':
        result=hybrid_planning_extension('hybrid-scene-0.4')
        result['version']=version
        result['grammars'].append('before_after')
        result['rules'].append('before_after: snapshot_pair of one explicitly named entity/metric/unit at two quoted times. No edges or intermediate samples; order is not causation. Nodes empty, common zero scale in pair only.')
        return result
    if version not in {"hybrid-scene-0.1", "hybrid-scene-0.2", "hybrid-scene-0.3", "hybrid-scene-0.4"}:
        raise ValueError("unsupported_hybrid_contract")
    result = {"version": version, "routes": ["cinematic", "diagram", "source"],
            "grammars": ["cause_change_result", "quantitative_comparison", "transport_track"],
            "rules": [
                "Every scene has layout.hybrid; emotional stakes use cinematic stills, relations use diagrams, authentic observations use registered sources.",
                "Select grammar from causal links, comparable quantities or movement between endpoints, not topic keywords.",
                "Source IDs must come from trusted_source_catalog; no model URLs, filenames or invented evidence.",
                "A modern source cannot prove a historical event. Preserve the catalog's date and meaning limitations.",
                "Only cinematic shots generate images. Diagrams are editable objects. Every route keeps source narration order.",
                "Coordinates and event times are normalized. Reserve final 15 percent for reading. Keep diagram labels concise.",
                "Comparison values must come from script or verified evidence; use a common unit and nontruncated scale.",
                "Only hard cuts between routes in this version; no fallback to a different route.",
            ]}
    if version in {"hybrid-scene-0.2", "hybrid-scene-0.3", "hybrid-scene-0.4"}:
        result["rules"] += [
            "Optional composition illustrated-transport-0.1 is only for transport_track diagrams with two endpoints and one edge.",
            "Select asset_pack_id only from trusted_illustration_catalog. Absent matching art means do not request composition; never substitute unrelated art.",
            "A composition is an explanatory beat, not an emotional portrait with arrows. Its generated plate is not source evidence.",
            "Use four monotonic cubic controls inside the catalog safe_rect with sprite clearance. Match node positions and edge times to composition.",
            "Composition camera is hold; subject width is normalized to the plate. No articulated acting or automatic land avoidance is supported.",
        ]
    if version in {"hybrid-scene-0.3", "hybrid-scene-0.4"}:
        result["grammars"] += ["cumulative_change", "step_sequence"]
        result["rules"] += [
            "Choose cumulative_change only for ordered nonnegative increments with a common unit. The renderer computes running sums; node.quantity is an increment, never the total.",
            "Choose step_sequence only for a stated ordered procedure, not a causal claim or category list. Nodes and edges form one ordered chain.",
            "For v0.3 comparisons/accumulations, source_quote must be an exact narration substring containing the numeric quantity with its exact unit. Invented values fail preflight.",
            "New semantic diagrams allow at most four short-labeled items; split complex explanations into adjacent beats without changing narration.",
        ]
    if version == "hybrid-scene-0.4":
        result["rules"] += [
            "Copy one film-design-0.1 to every scene. Same concept, route treatments, palette and typography; not aesthetic approval.",
            "Nodes/paths use palette accents. Text contrast >=4.5 on background/surface; lines/accents >=3 on background.",
            "Only cinematic stills support push/pull. Diagram/source camera is hold. Match artwork to design; no baked text or source pixel edits.",
        ]
    return result


def hybrid_enabled(contract):
    value = (contract or {}).get("hybrid_direction")
    if value is None:
        return False
    if not isinstance(value, dict) or value != hybrid_planning_extension(value.get("version")):
        raise ValueError("unsupported_hybrid_contract")
    return True


def hybrid_output_schema(base, contract):
    result = deepcopy(base)
    if not hybrid_enabled(contract):
        return result
    schema = HybridScene.model_json_schema()
    definitions = schema.pop("$defs", {})
    version = contract["hybrid_direction"]["version"]
    node_schema = definitions["DiagramNode"]
    if version in {"hybrid-scene-0.3", "hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"}:
        node_schema["properties"]["source_quote"].pop("default", None)
        node_schema["required"].append("source_quote")
    else:
        node_schema["properties"].pop("source_quote", None)
        definitions["Diagram"]["properties"]["grammar"]["enum"] = ["cause_change_result", "quantitative_comparison", "transport_track"]
    schema["properties"]["version"] = {"type": "string", "const": version}
    diagram_schema=definitions['Diagram']
    if version in {'hybrid-scene-0.5','hybrid-scene-0.6'}:
        diagram_schema['properties']['snapshot_pair'].pop('default',None)
        diagram_schema['required'].append('snapshot_pair')
    else:
        diagram_schema['properties'].pop('snapshot_pair')
        diagram_schema['properties']['nodes']['minItems']=2
        grammars=diagram_schema['properties']['grammar']['enum']
        if 'before_after' in grammars: grammars.remove('before_after')
        definitions.pop('SnapshotPair'); definitions.pop('MeasurementSnapshot')
    if version == 'hybrid-scene-0.6':
        diagram_schema['properties']['spatial_map'].pop('default',None)
        diagram_schema['required'].append('spatial_map')
    else:
        diagram_schema['properties'].pop('spatial_map')
        if 'map_spatial' in diagram_schema['properties']['grammar']['enum']:
            diagram_schema['properties']['grammar']['enum'].remove('map_spatial')
        for name in ('SpatialMap','SpatialPlace','SpatialRegion','SpatialRelation'):
            definitions.pop(name)
    if version in {"hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"}:
        selection_version = (contract.get('concept_selection') or {}).get('version')
        design_name = ('DirectedGraphicFilmDesign' if selection_version == 'concept-selection-0.3' else
                       'GraphicFilmDesign' if selection_version == 'concept-selection-0.2' else 'FilmDesign')
        schema["properties"]["design"] = {"$ref": f"#/$defs/{design_name}"}
        schema["required"].append("design")
    else:
        schema["properties"].pop("design", None)
        for name in ("FilmDesign", "GraphicFilmDesign", "DirectedGraphicFilmDesign", "FilmPalette", "FilmTypography"):
            definitions.pop(name, None)
    if contract["hybrid_direction"]["version"] == "hybrid-scene-0.1":
        schema["properties"].pop("composition", None)
        schema["properties"]["version"] = {"type": "string", "const": "hybrid-scene-0.1"}
    else:
        # Strict structured output requires every property; absence is explicit null.
        schema["properties"]["composition"].pop("default", None)
        schema["required"].append("composition")
    definitions["HybridScene"] = schema
    if set(definitions) & set(result["$defs"]):
        raise ValueError("hybrid_schema_collision")
    result["$defs"].update(definitions)
    layout = result["$defs"]["scene"]["properties"]["layout"]
    layout["properties"]["hybrid"] = {"$ref": "#/$defs/HybridScene"}
    layout["required"].append("hybrid")
    return result


def evaluate_hybrid(scenes, source_ids=None, illustration_ids=None, expected_version=None):
    findings = []
    try:
        shared_design(scenes)
    except (ValueError, ValidationError):
        findings.append("film_design_invalid_or_inconsistent")
    for scene in scenes:
        try:
            route = HybridScene.model_validate(scene.layout.get("hybrid"))
            if expected_version is not None and route.version != expected_version:
                findings.append(f"{scene.id}:hybrid_contract_version_mismatch")
            if route.diagram and route.diagram.snapshot_pair:
                findings.extend(f'{scene.id}:{finding}' for finding in route.diagram.snapshot_pair.grounding_findings(getattr(scene,'narration','')))
            if route.diagram and route.diagram.spatial_map:
                findings.extend(f'{scene.id}:{finding}' for finding in route.diagram.spatial_map.grounding_findings(getattr(scene,'narration','')))
            if route.version in {"hybrid-scene-0.3", "hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"} and route.diagram and route.diagram.grammar in {"quantitative_comparison", "cumulative_change"}:
                import re
                narration = getattr(scene, "narration", "")
                for node in route.diagram.nodes:
                    quote = node.source_quote or ""
                    number = re.escape(format(node.quantity, "g"))
                    unit = re.escape(node.unit or "")
                    if not quote or quote not in narration or not re.search(r"(?<![\d.,])" + number + r"\s*" + unit, quote):
                        findings.append(f"{scene.id}:{node.id}:quantity_not_grounded_in_narration")
            if scene.transition != "cut":
                findings.append(f"{scene.id}:hybrid_requires_cut")
            if route.version in {"hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"} and route.route != "cinematic":
                if (scene.layout.get("camera") or {}).get("mode", "hold") != "hold":
                    findings.append(f"{scene.id}:local_route_requires_fixed_camera")
            if route.route != "cinematic" and (getattr(scene, "reference_asset_ids", []) or getattr(scene, "present_asset_ids", [])):
                findings.append(f"{scene.id}:local_route_no_generated_references")
            if source_ids is not None and route.route == "source" and route.source_id not in source_ids:
                findings.append(f"{scene.id}:source_not_registered")
            if route.composition is not None:
                if illustration_ids is not None and route.composition.asset_pack_id not in illustration_ids:
                    findings.append(f"{scene.id}:illustration_not_registered")
                if (scene.layout.get("camera") or {}).get("mode", "hold") != "hold":
                    findings.append(f"{scene.id}:illustrated_transport_requires_fixed_camera")
        except ValidationError as error:
            # A location alone hides validator failures such as forbidden edges.
            # Exclude submitted input/context; only bounded validation reasons travel back.
            for item in error.errors(include_input=False, include_context=False, include_url=False)[:12]:
                location = ".".join(map(str, item["loc"])) or "root"
                reason = item["msg"].removeprefix("Value error, ")[:240]
                findings.append(f"{scene.id}:invalid_hybrid:{location}:{reason}")
    return findings
