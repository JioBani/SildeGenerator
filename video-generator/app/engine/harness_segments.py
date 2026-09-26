"""Validate optional creative segment boundaries before scheduling render work."""


def segment_ranges(harness, scenes, preferred_size):
    if type(preferred_size) is not int or preferred_size < 1:
        raise ValueError('preferred segment size must be a positive integer')
    planner = getattr(harness.instance, 'plan_segments', None)
    ranges = (planner(scenes, preferred_size, harness.config) if planner else
              [(start, min(start + preferred_size, len(scenes)))
               for start in range(0, len(scenes), preferred_size)])
    if not isinstance(ranges, list):
        raise TypeError('plan_segments must return a list of half-open ranges')
    cursor = 0
    for item in ranges:
        if not isinstance(item, (tuple, list)) or len(item) != 2 or any(type(n) is not int for n in item):
            raise ValueError('invalid segment range')
        start, end = item
        if start != cursor or not start < end <= len(scenes):
            raise ValueError('segment ranges must preserve every scene exactly once in order')
        cursor = end
    if cursor != len(scenes):
        raise ValueError('segment ranges omit scenes')
    return ranges
