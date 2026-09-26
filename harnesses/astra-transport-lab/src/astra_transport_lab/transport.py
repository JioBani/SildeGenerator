import math
import re


def compile_columns(scene):
    layout=getattr(scene,'layout',{}) or {}
    columns=layout.get('columns',[])
    if not isinstance(columns,list) or len(columns)>6:raise ValueError('Invalid transport columns')
    result=[]
    for column in columns:
        if not isinstance(column,dict):raise ValueError('Invalid column')
        x=column.get('x');label=column.get('label')
        if type(x) not in (int,float) or not math.isfinite(x) or not .05<=x<=.95:raise ValueError('Invalid column position')
        if not isinstance(label,str) or not 1<=len(label)<=24:raise ValueError('Invalid column label')
        result.append({'x':x,'label':label})
    return result


def compile_tracks(scene):
    size=(getattr(scene,'layout',{}) or {}).get('token_size','compact')
    if size not in ('compact','readable'):raise ValueError('Unknown token size profile')
    duration=float(scene.duration_seconds)
    if not math.isfinite(duration) or not 0<duration<=60:
        raise ValueError('Invalid transport scene duration')
    objects={}
    for item in getattr(scene,'object_states',[]) or []:
        if item.get('role')!='token':continue
        name=item.get('object_id','')
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}',name) or name in objects:
            raise ValueError('Invalid or duplicate token id')
        label=item.get('label',name)
        if not isinstance(label,str) or len(label)>20:raise ValueError('Invalid token label')
        events=item.get('performance_states',[])
        if not isinstance(events,list) or len(events)>32:raise ValueError('Invalid token states')
        clean_events=[]
        for event in events:
            if not isinstance(event,dict):raise ValueError('Invalid state event')
            t=event.get('time');state=event.get('state');text=event.get('label')
            if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=duration:raise ValueError('Invalid state time')
            if clean_events and t<=clean_events[-1]['time']:raise ValueError('State times must increase')
            if state not in ('queued','processing','complete'):raise ValueError('Unknown token state')
            if not isinstance(text,str) or len(text)>20:raise ValueError('Invalid state label')
            clean_events.append({'time':t,'state':state,'label':text})
        objects[name]={'id':name,'label':label,'states':clean_events,'size':size}
    if len(objects)>64:raise ValueError('Too many tokens')
    tracks=[]
    seen=set()
    for action in getattr(scene,'motion',[]) or []:
        if action.get('kind')!='transport_track':continue
        name=action.get('object_id')
        if name not in objects or name in seen:raise ValueError('Missing token or duplicate track')
        points=action.get('points')
        if not isinstance(points,list) or not 2<=len(points)<=600:raise ValueError('Invalid track sample count')
        clean=[]
        for p in points:
            values=[p.get(k) for k in ('time','x','y')]
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):raise ValueError('Nonfinite track sample')
            t,x,y=values
            if not 0<=t<=duration or not .05<=x<=.95 or not .08<=y<=.85:raise ValueError('Track outside time or safe canvas')
            if clean and t<=clean[-1]['time']:raise ValueError('Track time must strictly increase')
            clean.append({'time':t,'x':x,'y':y})
        tracks.append({**objects[name],'points':clean})
        seen.add(name)
    if set(objects)!=seen:raise ValueError('Token without transport track')
    return tracks
