import ckan.plugins.toolkit as tk
from ckan.lib.navl.dictization_functions import Missing


def approval_state_value(key, data, errors, context):

    state = data.get(key)

    if isinstance(state, Missing):
        return

    if state not in {'approved', 'pending', 'rejected', None}:
        raise tk.Invalid("Invalid approval state value")
