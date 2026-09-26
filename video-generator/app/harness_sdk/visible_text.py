"""Opt-in pre-render meaning review of generated diagram text, not film approval."""


def visible_text_extension():
    return {'version': 'visible-text-0.2', 'model': 'gpt-5.6-terra', 'max_repairs': 1}


def visible_text_enabled(contract):
    policy = (contract or {}).get('visible_text_review')
    if policy is None:
        return False
    if policy != visible_text_extension():
        raise ValueError('unsupported_visible_text_review')
    return True
