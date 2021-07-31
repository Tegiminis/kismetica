from perk import Perk, BasePerk
from buffhandler import add_buff

class Template(BasePerk):
    pass

class Rampage(BasePerk):
    trigger = 'kill'
    release = None
    slot = 'style1'

    def on_trigger(self, context):
        add_buff(context.db.buffhandler, 'Rampage')