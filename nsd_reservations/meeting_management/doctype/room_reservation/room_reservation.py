import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class RoomReservation(Document):
    def validate(self):
        self.validate_time()
        self.validate_active_room()
        self.validate_capacity()
        self.validate_overlap()

    def validate_time(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            frappe.throw("Start Time must be before End Time")

    def validate_active_room(self):
        if self.meeting_room:
            room = frappe.get_doc("Meeting Room", self.meeting_room)
            if not room.is_active:
                frappe.throw(f"Meeting Room {self.meeting_room} is inactive")

    def validate_capacity(self):
        if self.meeting_room and self.number_of_attendees:
            room = frappe.get_doc("Meeting Room", self.meeting_room)
            if room.capacity and self.number_of_attendees > room.capacity:
                frappe.throw(f"Attendees ({self.number_of_attendees}) exceed room capacity ({room.capacity})")

    def validate_overlap(self):
        if self.meeting_room and self.start_time and self.end_time:
            overlapping = frappe.db.get_all("Room Reservation",
                filters={
                    "meeting_room": self.meeting_room,
                    "docstatus": 1,
                    "start_time": ["<", self.end_time],
                    "end_time": [">", self.start_time],
                    "name": ["!=", self.name or ""]
                }
            )
            if overlapping:
                frappe.throw(f"Overlaps with approved reservation(s): {', '.join(r.name for r in overlapping)}")

    def on_submit(self):
        if self.docstatus == 1:
            self.approved_by = frappe.session.user
            self.approved_on = now_datetime()
            self.status = "Reserved"

    def on_cancel(self):
        self.status = "Cancelled"
