"""Fail closed when a production request still contains storyboard instructions."""
import re

_TIME_HEADER = re.compile(r"^[\[(]\s*\d{1,2}(?::\d{2})?\s*[~\u2013\u2014-]\s*\d{1,2}(?::\d{2})?\s*(?:초|s|sec)?\s*[\])]", re.I)
_LABEL = re.compile(r"^\W*(?:(?:영상|동영상|쇼츠)\s*)?(?:제목|화면|연출|카메라|자막|효과음|BGM|나레이션|내레이션|VO|V\.O\.)\s*[:：]", re.I)


def require_narration_only(text: str) -> None:
    for line in text.splitlines():
        plain = re.sub(r"[*_`]+", "", line).strip()
        plain = re.sub(r"^(?:[-+>]\s+)+", "", plain)
        if _TIME_HEADER.match(plain) or _LABEL.match(plain) or re.match(r"^#{1,6}\s+", plain):
            raise ValueError("음성 대본에 제목·시간표·연출 지시가 남아 있습니다. 원본 대본을 다시 접수해 나레이션만 추출해 주세요.")
