def _set_name(caller, raw_string, **kwargs):
    caller.db.chargen["name"] = raw_string

    return "chargen_main"

def chargen_main(caller, raw_string, **kwargs):

    text = "A test of the chargen menu"

    options = (
        {"key": None,
         "desc": "Name",
         "goto": "chargen_name"},

        {"key": None,
         "desc": "Eyes",
         "goto": "chargen_eyes"},

        {"key": None,
         "desc": "Hair",
         "goto": "chargen_hair"})

    return text, options

def chargen_name(caller, raw_string, **kwargs):

    text = "What is your name?"

    options = (
        {"key": _default,
         "goto": "_set_name"})

    return text, options

def chargen_eyes(caller, raw_string, **kwargs):

    text = "What color eyes do you have?"

    options = (
        {"key": None,
         "desc": "brown",
         "goto": "_set_eyes"},

        {"key": ("Defend", "d", "def"),
         "desc": "Hold back and defend yourself",
         "goto": (_defend, {"str": 10, "enemyname": "Goblin"})})

    return text, options