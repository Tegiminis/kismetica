class BuffList():

    Template = {
        'id': 'template',           # The buff's unique ID. Will be used as the buff's key in the handler
        'name': 'Template',         # The buff's name. Used for user messaging
        'flavor': 'Template',       # The buff's flavor text. Used for user messaging

        'refresh': True,            # Does the buff refresh its timer on application?
        'stacking': False,          # Does the buff stack with itself?
        'stat': 'damage',           # The stat the buff affects. Essentially a tag used to find the buff for coding purposes  
        'stacks': 1,                # The number of stacks the buff has. Defaults to 1
        'maxstacks': 1,             # The maximum number of stacks the buff can have.
        'duration': 1,              # Buff duration in seconds
        'base': 0,                  # Buff's value
        'perstack': 0,              # How much additional value is added to the buff per stack
        'mod': 'add' }              # The modifier the buff applies. 'add' or 'mult'               
    
    Rampage = {
        'id': 'rampage',
        'name': 'Rampage',
        'flavor': 'Increase damage for each enemy killed recently.',

        'refresh': True,
        'stacking': True,
        'stat': 'damage',
        'stacks': 1,
        'maxstacks': 5,
        'duration': 30,
        'base': 0.05,
        'perstack': 0,
        'mod': 'add' }

