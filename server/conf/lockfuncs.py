"""

Lockfuncs

Lock functions are functions available when defining lock strings,
which in turn limits access to various game systems.

All functions defined globally in this module are assumed to be
available for use in lockstrings to determine access. See the
Evennia documentation for more info on locks.

A lock function is always called with two arguments, accessing_obj and
accessed_obj, followed by any number of arguments. All possible
arguments should be handled with *args, **kwargs. The lock function
should handle all eventual tracebacks by logging the error and
returning False.

Lock functions in this module extend (and will overload same-named)
lock functions from evennia.locks.lockfuncs.

"""

# def myfalse(accessing_obj, accessed_obj, *args, **kwargs):
#    """
#    called in lockstring with myfalse().
#    A simple logger that always returns false. Prints to stdout
#    for simplicity, should use utils.logger for real operation.
#    """
#    print "%s tried to access %s. Access denied." % (accessing_obj, accessed_obj)
#    return False


def equipped(accessing_obj, accessed_obj, *args, **kwargs):
    if accessed_obj == accessing_obj.db.held:
        return True
    return False


def tagged(accessing_obj, accessed_obj, *args, **kwargs):
    """
    Usage:
        tag(tagkey)
        tag(tagkey, category)

    Identical to the lockfunc tag(), except it applies to the accessed object instead.
    """
    if hasattr(accessed_obj, "obj"):
        accessed_obj = accessed_obj.obj
    tagkey = args[0] if args else None
    category = args[1] if len(args) > 1 else None
    return accessed_obj.tags.has(tagkey, category=category)
