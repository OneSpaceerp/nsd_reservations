import frappe
import unittest
from frappe.utils import add_to_date, now_datetime

class TestRoomReservation(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.db.exists("Meeting Room", "Test Room"):
            self.room = frappe.get_doc({
                "doctype": "Meeting Room",
                "room_name": "Test Room",
                "capacity": 10,
                "is_active": 1
            }).insert()
        else:
            self.room = frappe.get_doc("Meeting Room", "Test Room")
        self.dept = frappe.get_value("Department", {}, "name")

    def test_create_reservation(self):
        start = add_to_date(now_datetime(), hours=1)
        end = add_to_date(start, hours=2)
        res = frappe.get_doc({
            "doctype": "Room Reservation",
            "meeting_room": self.room.name,
            "start_time": start,
            "end_time": end,
            "person_in_charge": "Administrator",
            "department": self.dept,
            "meeting_reason": "Test Meeting",
            "number_of_attendees": 5
        }).insert()
        self.assertEqual(res.status, "Draft")
        res.delete()

    def test_overlap_reservation(self):
        start = add_to_date(now_datetime(), hours=3)
        end = add_to_date(start, hours=2)
        res1 = frappe.get_doc({
            "doctype": "Room Reservation",
            "meeting_room": self.room.name,
            "start_time": start,
            "end_time": end,
            "person_in_charge": "Administrator",
            "department": self.dept,
            "meeting_reason": "Test Meeting 1",
            "number_of_attendees": 5
        }).insert()
        res1.submit()
        start2 = add_to_date(start, hours=1)
        end2 = add_to_date(end, hours=-1)
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Room Reservation",
                "meeting_room": self.room.name,
                "start_time": start2,
                "end_time": end2,
                "person_in_charge": "Administrator",
                "department": self.dept,
                "meeting_reason": "Test Meeting 2",
                "number_of_attendees": 5
            }).insert()
        res1.cancel()
        res1.delete()

    def test_capacity_validation(self):
        start = add_to_date(now_datetime(), hours=5)
        end = add_to_date(start, hours=2)
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Room Reservation",
                "meeting_room": self.room.name,
                "start_time": start,
                "end_time": end,
                "person_in_charge": "Administrator",
                "department": self.dept,
                "meeting_reason": "Test Meeting",
                "number_of_attendees": 15
            }).insert()

    def tearDown(self):
        frappe.set_user("Administrator")
