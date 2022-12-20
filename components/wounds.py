class WoundHandler():
    obj = None

    msg = {
        "light": {
            "bullet": [""],
            "energy": [""],
            "blunt": [""],
            "sharp": [""]
        },

        "heavy": {
            "bullet": [""],
            "energy": [""],
            "blunt": [""],
            "sharp": [""]
        },

        "severed": {
            "bullet": [""],
            "energy": [""],
            "blunt": [""],
            "sharp": [""]
        }
    }
    
    class WOUND_SEVERITY:
        none = 0
        light = 1
        heavy = 2
        severed = 3

    def __init__(self, obj) -> None:
        self.obj = obj

        if not obj.attributes.has('wounds'): 
            self.obj.db.wounds = {
                "head": 0,
                "chest": 0,
                "stomach": 0,
                "leftarm": 0,
                "rightarm": 0,
                "leftleg": 0,
                "rightleg": 0,
            }

    @property
    def db(self):
        return self.obj.db.wounds

    def wound():
        pass

    def heal():
        pass

    def _message_wound():
        pass