"""Fixed-location diagram: reveals knowledge, never animates places in space."""
import html


def point(place):
    return 130+place.x*740, 150+place.y*280


def markup(diagram,index,duration,cursor,design):
    spatial=diagram.spatial_map
    if spatial is None or design is None:
        raise ValueError('spatial_contract_and_design_required')
    events=[r.show_at for r in spatial.relations]
    if any(duration*(b-a) < 1.2 for a,b in zip(events,[*events[1:],1])):
        raise ValueError('spatial_relation_reading_hold_too_short')
    p=design.palette
    def text(value,x,y,size=22,anchor='middle',color=None):
        return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color or p.text}" font-size="{size}">{html.escape(value)}</text>'
    parts=[text('북',920,140,22),f'<path d="M920 190 V155 M911 167 L920 155 L929 167" fill="none" stroke="{p.line}" stroke-width="{design.line_width}"/>',
        text('상대 위치 도식 · 거리 비례 아님',500,450,18,color=p.secondary_text)]
    actions=[]
    shapes={}
    items={item.id:item for item in [*spatial.regions,*spatial.places]}
    for j,region in enumerate(spatial.regions):
        x,y=130+region.left*740,150+region.top*280
        w,h=(region.right-region.left)*740,(region.bottom-region.top)*280
        shape=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="0"/>'
        shapes[region.id]=shape
        parts.append(f'<g id="region-{index}-{j}" opacity="0"><g fill="none" stroke="{p.line}" stroke-width="{design.line_width}" stroke-dasharray="8 5">{shape}</g>{text(region.label,x+12,y+26,20,"start")}</g>')
        actions.append(f"tl.to('#region-{index}-{j}',{{opacity:1,duration:.25,ease:'power2.out'}},{cursor+duration*region.reveal_at});")
    for j,place in enumerate(spatial.places):
        x,y=point(place)
        shapes[place.id]=f'<circle cx="{x}" cy="{y}" r="19"/>'
        parts.append(f'<g id="place-{index}-{j}" opacity="0"><circle cx="{x}" cy="{y}" r="12" fill="{place.color}"/>{text(place.label,x,y+34)}</g>')
        actions.append(f"tl.to('#place-{index}-{j}',{{opacity:1,duration:.25,ease:'power2.out'}},{cursor+duration*place.reveal_at});")
    terms={'north_of':'북쪽','south_of':'남쪽','east_of':'동쪽','west_of':'서쪽','inside':'안','outside':'밖'}
    for j,relation in enumerate(spatial.relations):
        identifier=f'spatial-relation-{index}-{j}'
        label=f'{items[relation.subject].label} · {items[relation.target].label}의 {terms[relation.relation]}'
        parts.append(f'<g id="{identifier}" opacity="0"><g fill="none" stroke="{p.line}" stroke-width="{design.line_width+1}">{shapes[relation.subject]}{shapes[relation.target]}</g>{text(label,500,110,24)}</g>')
        start=cursor+duration*relation.show_at
        actions.append(f"tl.to('#{identifier}',{{opacity:1,duration:.25,ease:'power2.out'}},{start});")
        if j+1<len(spatial.relations):
            actions.append(f"tl.to('#{identifier}',{{opacity:0,duration:.15}},{cursor+duration*spatial.relations[j+1].show_at-.15});")
    title=html.escape(diagram.title)
    return f'<h2>{title}</h2><svg viewBox="0 0 1000 600" aria-label="{title}">{"".join(parts)}</svg>',actions


def poster(draw,spatial,width,height,font,palette):
    for region in spatial.regions:
        draw.rectangle((width*(.13+region.left*.74),height*(.25+region.top*.4667),
                        width*(.13+region.right*.74),height*(.25+region.bottom*.4667)),outline=palette.line,width=3)
    for place in spatial.places:
        x,y=point(place); x*=width/1000; y*=height/600
        draw.ellipse((x-10,y-10,x+10,y+10),fill=place.color)
        draw.text((x,y+20),place.label,fill=palette.text,font=font,anchor='mt')
    draw.text((width*.5,height*.82),'상대 위치 도식 · 거리 비례 아님',fill=palette.text,font=font,anchor='mt')
