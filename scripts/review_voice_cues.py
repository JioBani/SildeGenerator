"""Caption windows from SAPI's actual word events, not estimated speaking rate."""
import re


def align_spatial_events(diagram,narration,words,duration):
    """Retain geometry; bind relationship emphasis to measured direct clauses."""
    if duration<=0: raise ValueError('measured_duration_required')
    spatial=diagram['spatial_map']; anchors=[]
    items={p['id']:p for p in [*spatial['places'],*spatial['regions']]}
    reveal={key:1 for key in items}
    for relation in spatial['relations']:
        quote=relation['source_quote']
        if narration.count(quote)!=1: raise ValueError('spatial_quote_alignment_ambiguous')
        position=narration.index(quote)
        event=next((w for w in words if w['start']<=position<w['start']+w['length']),None)
        if event is None or not 0<=event['seconds']<duration: raise ValueError('spatial_voice_alignment_missing')
        planned=relation['show_at']; relation['show_at']=event['seconds']/duration
        for key in (relation['subject'],relation['target']):
            reveal[key]=min(reveal[key],max(0,relation['show_at']-.055))
        anchors.append(dict(subject=relation['subject'],target=relation['target'],quote=quote,seconds=event['seconds'],
            planned=dict(show_at=planned),measured=dict(show_at=relation['show_at'])))
    for key,item in items.items(): item['reveal_at']=reveal[key]
    return anchors


def align_quantity_events(diagram, narration, words, duration):
    """Anchor numeric reveals to observed speech, without replacing semantic values."""
    if diagram['grammar']=='before_after':
        if duration<=0: raise ValueError('measured_duration_required')
        anchors=[]
        for name in ('before','after'):
            state=diagram['snapshot_pair'][name]; quote=state['source_quote']
            if not quote or narration.count(quote)!=1:
                raise ValueError('quantity_quote_alignment_ambiguous')
            position=narration.index(quote)
            word=next((w for w in words if w['start']<=position<w['start']+w['length']),None)
            if word is None or not 0<=word['seconds']<duration:
                raise ValueError('quantity_voice_alignment_missing')
            old=state['show_at']; state['show_at']=word['seconds']/duration
            anchors.append(dict(node_id=name,quote=quote,seconds=word['seconds'],
                planned=dict(show_at=old),measured=dict(show_at=state['show_at'])))
        return anchors
    if diagram['grammar'] not in {'quantitative_comparison','cumulative_change'}:
        return []
    if duration <= 0:
        raise ValueError('measured_duration_required')
    anchors=[]
    for node in diagram['nodes']:
        quote=node.get('source_quote') or ''
        if not quote or narration.count(quote)!=1:
            raise ValueError('quantity_quote_alignment_ambiguous')
        position=narration.index(quote)
        word=next((w for w in words if w['start']<=position<w['start']+w['length']),None)
        if word is None or not 0<=word['seconds']<duration:
            raise ValueError('quantity_voice_alignment_missing')
        old=dict(reveal_at=node['reveal_at'],change_at=node['change_at'])
        node['change_at']=word['seconds']/duration
        node['reveal_at']=max(0,node['change_at']-.08)
        anchors.append(dict(node_id=node['id'],quote=quote,seconds=word['seconds'],planned=old,
            measured=dict(reveal_at=node['reveal_at'],change_at=node['change_at'])))
    return anchors


def caption_cues(narration, words, duration):
    if not words or words[0]["seconds"] < 0 or words[-1]["seconds"] >= duration:
        raise ValueError("missing_voice_alignment")
    if any(b["seconds"]<a["seconds"] for a,b in zip(words,words[1:])):
        raise ValueError("unordered_voice_alignment")
    # Preserve all original text; use punctuation/word boundaries for short cues.
    boundaries=[0]
    for word in words[1:]:
        position=word["start"]
        previous=narration[boundaries[-1]:position]
        if (len(previous.strip())>=12 and re.search(r"[.,!?]\s*$",previous)) or len(previous)>=26:
            boundaries.append(position)
    chunks=[]
    for i,start in enumerate(boundaries):
        end=boundaries[i+1] if i+1<len(boundaries) else len(narration)
        matching=next((w for w in words if w["start"]>=start),None)
        if matching is None: raise ValueError("caption_alignment_gap")
        chunks.append(dict(start=matching["seconds"],text=narration[start:end].strip()))
    for i,chunk in enumerate(chunks):
        chunk["end"]=chunks[i+1]["start"] if i+1<len(chunks) else duration
        if chunk["end"]<=chunk["start"]: raise ValueError("empty_caption_window")
        if chunk["end"]-chunk["start"] < max(1.2,len(chunk["text"])/8):
            raise ValueError("caption_reading_hold_insufficient")
    if re.sub(r"\s+","",''.join(c["text"] for c in chunks))!=re.sub(r"\s+","",narration):
        raise ValueError("caption_text_loss")
    return chunks
