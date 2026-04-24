import frappe
from frappe.model.document import Document


class MeetingRoom(Document):
    def validate(self):
        self.validate_unique_room_name()

    def validate_unique_room_name(self):
        if self.room_name:
            existing_room = frappe.db.exists(
                "Meeting Room",
                {
                    "room_name": self.room_name,
                    "name": ("!=", self.name),
                },
            )
            if existing_room:
                frappe.throw(
                    frappe._("A meeting room with name {0} already exists").format(
                        frappe.bold(self.room_name)
                    )
                )

    def before_insert(self):
        if not self.sort_order:
            self.sort_order = 0

    def before_save(self):
        if not self.get("__islocal"):
            self.check_room_reservations_on_deactivate()

    def check_room_reservations_on_deactivate(self):
        if self.has_value_changed("is_active") and not self.is_active:
            active_reservations = frappe.db.count(
                "Room Reservation",
                {
                    "meeting_room": self.name,
                    "workflow_state": "Reserved",
                    "docstatus": 1,
                },
            )
            if active_reservations > 0:
                frappe.throw(
                    frappe._(
                        "Cannot deactivate room {0} as it has {1} active reservation(s)"
                    ).format(
                        frappe.bold(self.room_name), frappe.bold(active_reservations)
                    )
                )