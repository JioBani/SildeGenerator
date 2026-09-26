"""Executable shared design, not aesthetic approval or concept selection."""
import hashlib
import json
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .direction import DirectionModel

Color = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
Description = Annotated[str, Field(min_length=12, max_length=600)]


def contrast(a, b):
    def luminance(color):
        values = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values]
        return sum(v*w for v, w in zip(linear, (.2126, .7152, .0722)))
    low, high = sorted((luminance(a), luminance(b)))
    return (high+.05)/(low+.05)


class FilmPalette(DirectionModel):
    background: Color
    text: Color
    secondary_text: Color
    surface: Color
    line: Color
    accents: list[Color] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def readable(self):
        for color in (self.text, self.secondary_text):
            if any(contrast(color, bg) < 4.5 for bg in (self.background, self.surface)):
                raise ValueError("film_text_contrast_below_4_5")
        if any(contrast(color, self.background) < 3 for color in [self.line, *self.accents]):
            raise ValueError("film_graphic_contrast_below_3")
        if len({color.lower() for color in self.accents}) != len(self.accents):
            raise ValueError("film_duplicate_accents")
        return self


class FilmTypography(DirectionModel):
    font: Literal["Noto Sans CJK KR"]
    # CSS values at 1280x720; diagrams retain their fixed SVG label geometry.
    title_px: int = Field(strict=True, ge=28, le=38)
    caption_px: int = Field(strict=True, ge=32, le=42)
    caption_margin_y: int = Field(strict=True, ge=42, le=64)


class FilmDesign(DirectionModel):
    version: Literal["film-design-0.1"]
    concept_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    central_idea: Description
    cinematic_language: Description
    diagram_language: Description
    source_treatment: Description
    palette: FilmPalette
    typography: FilmTypography
    line_width: int = Field(strict=True, ge=2, le=5)


class GraphicFilmDesign(FilmDesign):
    version: Literal["film-design-0.2"]
    snapshot_layout: Literal["columns", "rows", "dot_tracks"]


class DirectedGraphicFilmDesign(GraphicFilmDesign):
    version: Literal["film-design-0.3"]
    comparison_layout: Literal["rows", "columns", "dot_tracks"]
    type_treatment: Literal["documentary", "editorial", "explainer"]


FilmDesignContract = FilmDesign | GraphicFilmDesign | DirectedGraphicFilmDesign


def parse_design(value):
    model = {"film-design-0.1": FilmDesign, "film-design-0.2": GraphicFilmDesign,
             "film-design-0.3": DirectedGraphicFilmDesign}.get(value.get("version"))
    if model is None:
        raise ValueError("unsupported_film_design_version")
    return model.model_validate(value)


def design_sha256(design):
    return hashlib.sha256(json.dumps(design.model_dump(mode="json"), ensure_ascii=False,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def shared_design(scenes):
    """Reject mixed versions or drift even across separately rendered segments."""
    designs = []
    for scene in scenes:
        value = (scene.layout.get("hybrid") or {}).get("design")
        designs.append(parse_design(value) if value is not None else None)
    active = [d for d in designs if d is not None]
    if not active:
        return None
    if len(active) != len(designs) or len({design_sha256(d) for d in active}) != 1:
        raise ValueError("film_design_must_match_every_scene")
    return active[0]
