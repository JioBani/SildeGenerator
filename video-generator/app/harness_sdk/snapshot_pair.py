"""Two grounded measurements of one referent, without inferred causality."""
import re
from pydantic import Field, model_validator
from .direction import DirectionModel


class MeasurementSnapshot(DirectionModel):
    time_label: str = Field(min_length=1, max_length=12)
    value: float = Field(ge=0, le=1e12)
    source_quote: str = Field(min_length=1, max_length=240)
    show_at: float = Field(ge=0, le=.75)


class SnapshotPair(DirectionModel):
    version: str = Field(pattern=r"^snapshot-pair-0\.1$")
    entity: str = Field(min_length=1, max_length=20)
    metric: str = Field(min_length=1, max_length=16)
    unit: str = Field(min_length=1, max_length=8)
    scale_max: float = Field(gt=0, le=1e12)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    before: MeasurementSnapshot
    after: MeasurementSnapshot

    @model_validator(mode='after')
    def coherent(self):
        if self.after.show_at <= self.before.show_at or self.before.time_label == self.after.time_label:
            raise ValueError('snapshot_pair_requires_distinct_ordered_times')
        if max(self.before.value,self.after.value) > self.scale_max:
            raise ValueError('snapshot_pair_scale_truncates_value')
        if len(format(self.scale_max,'g'))>10:
            raise ValueError('snapshot_pair_scale_label_too_long')
        for snapshot in (self.before,self.after):
            if len(f'{snapshot.value:g} {self.unit}') > 12:
                raise ValueError('snapshot_pair_value_label_too_long')
            if any(word not in snapshot.source_quote for word in (self.entity,self.metric,snapshot.time_label)):
                raise ValueError('snapshot_pair_identity_metric_time_not_in_quote')
            number=re.escape(format(snapshot.value,'g'))
            if not re.search(r'(?<![\d.,])'+number+r'\s*'+re.escape(self.unit),snapshot.source_quote):
                raise ValueError('snapshot_pair_value_not_in_quote')
        return self

    def grounding_findings(self,narration):
        positions=[narration.find(s.source_quote) for s in (self.before,self.after)]
        if min(positions)<0:
            return ['snapshot_pair_quote_not_in_narration']
        if positions[1]<positions[0]+len(self.before.source_quote):
            return ['snapshot_pair_source_times_not_ordered']
        return []
