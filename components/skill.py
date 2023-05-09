from evennia.utils import search


class SkillHandler(object):
    ownerref = None
    dbkey = "skills"
    autopause = False

    def __init__(self, owner, dbkey=dbkey, autopause=autopause):
        self.ownerref = owner.dbref
        self.dbkey = dbkey
        self.autopause = autopause

    @property
    def owner(self):
        """The object this handler is attached to"""
        return search.search_object(self.ownerref)[0]
