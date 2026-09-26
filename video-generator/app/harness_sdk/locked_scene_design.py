"""Core-owned meaning/design bindings, with one explicit creative slot per beat.

The wire format retains director-authored sequence/group boundaries, but refers
to immutable beat IDs instead of allocating or rewriting source-unit counts.
"""
from copy import deepcopy


def locked_scene_extension():
    # Detailed instructions are emitted once by Core alongside its wire schema.
    return {"version": "locked-scene-design-0.1", "ownership": "core"}


def locked_scene_enabled(contract):
    value=(contract or {}).get('locked_scene_design')
    if value is None: return False
    if value != locked_scene_extension(): raise ValueError('unsupported_locked_scene_design')
    required={'semantic_analysis':'semantic-beats-0.2',
              'narrative_direction':'narrative-direction-0.2'}
    if any((contract.get(k) or {}).get('version')!=v for k,v in required.items()) or not contract.get('concept_selection') or (contract.get('hybrid_direction') or {}).get('version') not in {'hybrid-scene-0.4','hybrid-scene-0.5','hybrid-scene-0.6'}:
        raise ValueError('locked_scene_design_requires_meaning_concept_and_design')
    return True


def beat_keys(analysis):
    return [f'beat-{i:03d}' for i in range(1,len(analysis.beats)+1)]


def _remove(schema,*names):
    for name in names:
        schema['properties'].pop(name,None)
        if name in schema['required']: schema['required'].remove(name)


def locked_scene_schema(base,analysis):
    result=deepcopy(base); defs=result['$defs']; keys=beat_keys(analysis)
    group=defs['group']; _remove(group,'scenes')
    group['properties']['beat_ids']={'type':'array','minItems':1,'maxItems':len(keys),
                                     'items':{'type':'string','enum':keys}}
    group['required'].append('beat_ids')
    entries={}
    for index,(key,beat) in enumerate(zip(keys,analysis.beats),1):
        draft=deepcopy(defs['scene'])
        _remove(draft,'source_unit_count','transition')
        layout=draft['properties']['layout']
        _remove(layout,'hybrid','authored_design','visual_labels')
        direction=deepcopy(defs['ShotDirection']); _remove(direction,'version')
        allowed=sorted({index}|{r.from_beat_number for r in beat.relations if r.kind in {'event_cause','motivation'}})
        direction['properties']['cause_scene_number']={'anyOf':[{'type':'null'},{'type':'integer','enum':allowed}]}
        layout['properties']['direction']=direction
        if beat.route!='cinematic': _remove(layout,'camera')
        if beat.route=='diagram':
            diagram=deepcopy(defs['Diagram']); _remove(diagram,'grammar')
            if beat.grammar == 'map_spatial':
                if 'spatial_map' not in diagram['properties']:
                    raise ValueError('map_spatial_requires_new_contract')
                _remove(diagram,'nodes','edges','comparison_scale_max','snapshot_pair')
                diagram['properties']['title']['maxLength']=26
                diagram['properties']['spatial_map']={'$ref':'#/$defs/SpatialMap'}
            elif beat.grammar == 'before_after':
                if 'snapshot_pair' not in diagram['properties']:
                    raise ValueError('before_after_requires_new_contract')
                _remove(diagram,'nodes','edges','comparison_scale_max')
                diagram['properties']['title']['maxLength']=26
                diagram['properties']['snapshot_pair']={'$ref':'#/$defs/SnapshotPair'}
            elif 'snapshot_pair' in diagram['properties']:
                _remove(diagram,'snapshot_pair')
                diagram['properties']['nodes']['minItems']=2
            if beat.grammar != 'map_spatial':
                _remove(diagram,'spatial_map')
            if beat.grammar in {'quantitative_comparison','cumulative_change'}:
                diagram['properties']['edges']['maxItems']=0
            props={'diagram':diagram}
            if beat.grammar=='transport_track':
                props['composition']=deepcopy(defs['HybridScene']['properties']['composition'])
            layout['properties']['hybrid']={'type':'object','additionalProperties':False,
                                           'properties':props,'required':list(props)}
            layout['required'].append('hybrid')
        name=f'BeatDesign{index}'; defs[name]=draft
        entries[key]={'$ref':f'#/$defs/{name}'}
    result['properties']['beat_designs']={'type':'object','additionalProperties':False,
                                        'properties':entries,'required':keys}
    result['required'].append('beat_designs')
    # Drop unreachable definitions, especially repeated full design contracts.
    needed=set()
    def visit(value):
        if isinstance(value,dict):
            reference=value.get('$ref')
            if reference and reference.startswith('#/$defs/'):
                name=reference.rsplit('/',1)[1]
                if name not in needed: needed.add(name); visit(defs[name])
            for k,v in value.items():
                if k!='$defs': visit(v)
        elif isinstance(value,list):
            for v in value: visit(v)
    visit(result)
    result['$defs']={k:v for k,v in defs.items() if k in needed}
    return result


def expand_locked_scene_proposal(proposal,analysis,concept,*,hybrid_version='hybrid-scene-0.4'):
    """Reject attempted ownership changes before lossless expansion to the old IR."""
    if hybrid_version not in {'hybrid-scene-0.4','hybrid-scene-0.5','hybrid-scene-0.6'}:
        raise ValueError('unsupported_locked_hybrid_version')
    result=deepcopy(proposal); keys=beat_keys(analysis)
    drafts=result.pop('beat_designs',None)
    if not isinstance(drafts,dict) or set(drafts)!=set(keys):
        raise ValueError('locked_beat_design_coverage_not_exact')
    groups=[g for s in result['sequences'] for g in s['scene_groups']]
    references=[]
    for group in groups:
        if 'scenes' in group: raise ValueError('locked_group_cannot_supply_scenes')
        ids=group.pop('beat_ids',None)
        if not isinstance(ids,list) or not ids: raise ValueError('locked_group_requires_beat_ids')
        references.extend(ids)
        group['scenes']=ids
    if references!=keys: raise ValueError('locked_beat_references_must_cover_source_once_in_order')
    bound={}
    for key,beat in zip(keys,analysis.beats):
        scene=drafts[key]; layout=scene['layout']
        if any(k in scene for k in ('source_unit_count','transition','narration','source_unit_ids')):
            raise ValueError(f'{key}:locked_scene_field_override')
        if any(k in layout for k in ('semantic_beat','selected_concept','authored_design','visual_labels')):
            raise ValueError(f'{key}:locked_layout_field_override')
        direction=layout['direction']
        if 'version' in direction: raise ValueError(f'{key}:locked_direction_version_override')
        direction['version']='narrative-direction-0.2'
        fragment=layout.pop('hybrid',{})
        allowed={'diagram'} if beat.route=='diagram' else set()
        if beat.grammar=='transport_track': allowed.add('composition')
        if not isinstance(fragment,dict) or set(fragment)!=allowed:
            raise ValueError(f'{key}:locked_hybrid_field_override_or_missing')
        diagram=fragment.get('diagram')
        if diagram is not None:
            if 'grammar' in diagram: raise ValueError(f'{key}:locked_grammar_override')
            diagram['grammar']=beat.grammar
            if beat.grammar in {'before_after','map_spatial'}:
                versions={'hybrid-scene-0.6'} if beat.grammar=='map_spatial' else {'hybrid-scene-0.5','hybrid-scene-0.6'}
                if hybrid_version not in versions or any(k in diagram for k in ('nodes','edges','comparison_scale_max')):
                    raise ValueError(f'{key}:locked_pair_structure_override')
                diagram.update(nodes=[],edges=[],comparison_scale_max=None)
        elif beat.route=='diagram': raise ValueError(f'{key}:locked_diagram_missing')
        if beat.route!='cinematic':
            if 'camera' in layout: raise ValueError(f'{key}:locked_local_camera_override')
            layout['camera']={'mode':'hold','focus':[.5,.5],'strength':0}
        sources={e.source_id for e in beat.required_evidence}
        if beat.route=='source' and (len(sources)!=1 or None in sources):
            raise ValueError(f'{key}:locked_source_not_resolved')
        layout.update(authored_design=None,visual_labels=[])
        layout['hybrid']={'version':hybrid_version,'route':beat.route,
            'reason':beat.route_reason,'diagram':diagram,
            'source_id':next(iter(sources)) if beat.route=='source' else None,
            'composition':fragment.get('composition'),'design':concept.design.model_dump(mode='json')}
        scene.update(source_unit_count=1,transition='cut')
        bound[key]=scene
    for group in groups: group['scenes']=[bound[key] for key in group['scenes']]
    return result
