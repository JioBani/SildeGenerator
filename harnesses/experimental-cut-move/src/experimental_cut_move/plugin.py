from classic_slide.plugin import ClassicSlideHarness
from .effects.cut_move import TRANSITION_NAME


class ExperimentalCutMoveHarness(ClassicSlideHarness):
    transition = TRANSITION_NAME
