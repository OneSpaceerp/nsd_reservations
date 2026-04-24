from frappe import _

def get_data():
    return {
        "name": "Meeting Management",
        "label": _("Meeting Management"),
        "icon": "fa fa-calendar",
        "color": "blue",
        "type": "module",
        "modules": ["Meeting Management"]
    }
