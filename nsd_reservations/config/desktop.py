import frappe


def get_data():
    return [
        {
            "module_name": "Meeting Management",
            "color": "Blue",
            "icon": "fa fa-calendar",
            "type": "module",
            "label": "Meeting Management",
        }
    ]


@frappe.whitelist()
def get_customers():
    return []