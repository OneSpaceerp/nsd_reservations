import frappe
from frappe.model.document import Document

class MeetingRoom(Document):
    def validate(self):
        if frappe.db.exists("Meeting Room", {"room_name": self.room_name, "name": ["!=", self.name]}):
            frappe.throw(f"Meeting Room {self.room_name} already exists")

    def before_save(self):
        if not hasattr(self, 'is_active'):
            self.is_active = 1
