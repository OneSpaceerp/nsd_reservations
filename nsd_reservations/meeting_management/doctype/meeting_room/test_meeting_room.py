import frappe
import unittest

class TestMeetingRoom(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")

    def test_create_meeting_room(self):
        room = frappe.get_doc({
            "doctype": "Meeting Room",
            "room_name": "Main Meeting Room",
            "capacity": 10,
            "is_active": 1
        }).insert()
        self.assertEqual(room.room_name, "Main Meeting Room")
        room.delete()

    def test_unique_room_name(self):
        room1 = frappe.get_doc({
            "doctype": "Meeting Room",
            "room_name": "Test Room",
            "is_active": 1
        }).insert()
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "Meeting Room",
                "room_name": "Test Room",
                "is_active": 1
            }).insert()
        room1.delete()

    def test_inactive_room(self):
        room = frappe.get_doc({
            "doctype": "Meeting Room",
            "room_name": "Inactive Room",
            "is_active": 0
        }).insert()
        self.assertEqual(room.is_active, 0)
        room.delete()
