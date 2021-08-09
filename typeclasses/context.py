class Context():
    '''A container for "context" information. Base class is a relation between two objects: actor and acted upon.'''
    actor = None
    actee = None
    
    def __init__(self, actor, actee) -> None:
        self.actor = actor
        self.actee = actee

class HitContext(Context):
    '''A container for an individual "hit context", which includes information about the weapon, target, etc.'''
    pass

def generate_context() -> Context:
    pass