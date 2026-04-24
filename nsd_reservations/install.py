import os
import frappe
from frappe.utils import get_site_path


def install():
    frappe.reload_doc("Meeting Management", "DocType", "Meeting Room")
    frappe.reload_doc("Meeting Management", "DocType", "Room Reservation")
    frappe.db.commit()


def after_install():
    create_roles()
    create_default_rooms()


def create_roles():
    roles = [
        {"name": "Meeting Room User", "desk_access": 1, "is_custom": 1},
        {"name": "Meeting Room Manager", "desk_access": 1, "is_custom": 1},
    ]
    for role_data in roles:
        if not frappe.db.exists("Role", role_data["name"]):
            role = frappe.get_doc({"doctype": "Role", **role_data})
            role.insert(ignore_permissions=True)


def create_default_rooms():
    default_rooms = [
        {"room_name": "Main Meeting Room", "capacity": 20, "is_active": 1, "location": "Floor 1"},
        {"room_name": "Casual Meeting Room", "capacity": 6, "is_active": 1, "location": "Floor 2"},
    ]
    for room_data in default_rooms:
        if not frappe.db.exists("Meeting Room", room_data["room_name"]):
            room = frappe.get_doc({"doctype": "Meeting Room", **room_data})
            room.insert(ignore_permissions=True)