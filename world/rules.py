def verify_context(context: dict = None):
    """Boilerplate for either creating a new context or setting one up."""
    if not context:
        context = {}
    else:
        context = dict(context)
    return context


def find_scripts_by_tag(obj, tag):
    _list = [x for x in obj.scripts.all() if tag in x.tags.all()]
    return _list


def capitalize(string: str, respect: bool = True):
    """
    Capitalizes the first letter of a string. Respects existing capitalization.

    Args:
        string:     String to capitalize
        respect:    (default: True) Determines if capitalization respects existing caps
    """
    if not string:
        return ""
    if not respect:
        return string.capitalize()
    strings = string.split()
    caps = [s.capitalize() if i == 0 else s for i, s in enumerate(strings)]
    ret = " ".join(caps)
    return ret


def check_time(start, end, duration):
    """Check to see if duration time has passed between the start and end time.
    Used for checking cooldowns or buff timing.

    Always returns false if duration is -1 (for things that last forever)."""

    if duration == -1 or not (duration and start and end):
        return False
    if duration < end - start:
        return True
    else:
        return False
