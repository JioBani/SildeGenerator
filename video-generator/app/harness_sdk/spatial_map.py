"""Relative schematic geography, not surveyed coordinates or transport animation."""
from typing import Annotated, Literal
import re
from pydantic import Field, model_validator
from .direction import DirectionModel

ID = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_-]{0,63}$')]
Label = Annotated[str, Field(min_length=1, max_length=10)]
Quote = Annotated[str, Field(min_length=1, max_length=240)]


class SpatialPlace(DirectionModel):
    id: ID
    label: Label
    x: float = Field(ge=.08, le=.92)
    y: float = Field(ge=.08, le=.86)
    reveal_at: float = Field(ge=0, le=.65)
    color: str = Field(pattern=r'^#[0-9a-fA-F]{6}$')


class SpatialRegion(DirectionModel):
    id: ID
    label: Label
    left: float = Field(ge=0, le=.6)
    top: float = Field(ge=0, le=.6)
    right: float = Field(ge=.4, le=1)
    bottom: float = Field(ge=.4, le=1)
    reveal_at: float = Field(ge=0, le=.65)

    @model_validator(mode='after')
    def extent(self):
        if self.right-self.left < .35 or self.bottom-self.top < .4:
            raise ValueError('spatial_region_too_small_for_label_and_content')
        return self


class SpatialRelation(DirectionModel):
    subject: ID
    target: ID
    relation: Literal['north_of', 'south_of', 'east_of', 'west_of', 'inside', 'outside']
    source_quote: Quote = Field(description='Exact standalone direct clause naming subject and target: Korean A는 B의 북쪽에 있습니다 / A는 B 안에 있습니다, or English A is north of B / A is inside B. Negated, conditional or implicit relations need another supported plan, not assertion.')
    show_at: float = Field(ge=.1, le=.75)


class SpatialMap(DirectionModel):
    version: Literal['spatial-map-0.1']
    coordinate_mode: Literal['relative_schematic_north_up']
    places: list[SpatialPlace] = Field(min_length=2, max_length=6)
    regions: list[SpatialRegion] = Field(max_length=2)
    relations: list[SpatialRelation] = Field(min_length=1, max_length=6)

    @model_validator(mode='after')
    def geometry(self):
        places = {p.id: p for p in self.places}
        regions = {r.id: r for r in self.regions}
        all_items = [*self.places, *self.regions]
        if len({i.id for i in all_items}) != len(all_items) or len({i.label for i in all_items}) != len(all_items):
            raise ValueError('spatial_identity_or_label_duplicate')
        for index, a in enumerate(self.places):
            for b in self.places[index+1:]:
                # Conservative fixed-font bounds; actual glyph boxes are tested after render.
                if abs(a.x-b.x)*740 < (len(a.label)+len(b.label))*11+24 and abs(a.y-b.y)*280 < 64:
                    raise ValueError('spatial_place_labels_overlap')
            for r in self.regions:
                # No marker or its label may sit on a region boundary/header.
                x, y = 130+a.x*740, 150+a.y*280
                left, right = 130+r.left*740, 130+r.right*740
                top, bottom = 150+r.top*280, 150+r.bottom*280
                half = max(14, len(a.label)*11)
                box = (x-half-6, y-18, x+half+6, y+40)
                intersects = box[2] >= left and box[0] <= right and box[3] >= top and box[1] <= bottom
                contained = box[0] > left+4 and box[2] < right-4 and box[1] > top+34 and box[3] < bottom-4
                if intersects and not contained:
                    raise ValueError('spatial_place_intersects_region_border_or_header')
        for i, a in enumerate(self.regions):
            for b in self.regions[i+1:]:
                if a.left < b.right and b.left < a.right and a.top < b.bottom and b.top < a.bottom:
                    raise ValueError('spatial_overlapping_regions_not_supported')
        covered = set()
        seen = set()
        previous = -1
        for relation in self.relations:
            subject = places.get(relation.subject)
            target = (regions if relation.relation in {'inside','outside'} else places).get(relation.target)
            key = (relation.subject, relation.target, relation.relation)
            if subject is None or target is None or subject.id == target.id or key in seen:
                raise ValueError('spatial_relation_invalid_referents')
            seen.add(key)
            covered.update((subject.id,target.id))
            if relation.show_at < max(subject.reveal_at,target.reveal_at)+.04 or relation.show_at < previous+.08:
                raise ValueError('spatial_relation_before_referents_or_reading_order')
            previous = relation.show_at
            if relation.relation == 'north_of': valid = subject.y < target.y-.15
            elif relation.relation == 'south_of': valid = subject.y > target.y+.15
            elif relation.relation == 'east_of': valid = subject.x > target.x+.15
            elif relation.relation == 'west_of': valid = subject.x < target.x-.15
            else:
                inside = target.left < subject.x < target.right and target.top < subject.y < target.bottom
                valid = inside if relation.relation == 'inside' else not inside
            if not valid:
                raise ValueError('spatial_relation_coordinate_contradiction')
        if covered != {item.id for item in all_items}:
            raise ValueError('spatial_unexplained_objects')
        return self

    def grounding_findings(self, narration):
        findings = []
        items = {item.id:item for item in [*self.places,*self.regions]}
        previous = -1
        for index, relation in enumerate(self.relations):
            quote = relation.source_quote
            location = narration.find(quote)
            if location < 0 or any(items[i].label not in quote for i in (relation.subject,relation.target)):
                findings.append(f'spatial_relation_{index}_quote_or_referents_not_grounded')
            if not direct_relation_quote(quote,items[relation.subject].label,items[relation.target].label,relation.relation):
                findings.append(f'spatial_relation_{index}_direction_not_grounded_in_direct_clause')
            if location < previous:
                findings.append(f'spatial_relation_{index}_source_order_reversed')
            previous = location
        return findings


def direct_relation_quote(quote,subject,target,kind):
    """Fail closed on negation/implicit language, rather than checking direction keywords."""
    subject,target=re.escape(subject),re.escape(target)
    ko={'north_of':'북쪽','south_of':'남쪽','east_of':'동쪽','west_of':'서쪽','inside':'안','outside':'밖'}[kind]
    en={'north_of':'north of','south_of':'south of','east_of':'east of','west_of':'west of','inside':'inside','outside':'outside'}[kind]
    korean=rf'{subject}(?:은|는|이|가)\s+{target}(?:의)?\s+{ko}에\s+(?:있습니다|있다|위치합니다|위치한다)[.!]?'
    english=rf'{subject}\s+is\s+(?:to the\s+)?{en}\s+{target}[.!]?'
    return bool(re.fullmatch(korean,quote.strip()) or re.fullmatch(english,quote.strip(),flags=re.IGNORECASE))
