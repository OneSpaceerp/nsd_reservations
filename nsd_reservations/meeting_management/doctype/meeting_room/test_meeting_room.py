import frappe
import unittest


class TestMeetingRoom(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")

    def test_create_meeting_room(self):
        room = frappe.get_doc(
            {
                "doctype": "Meeting Room",
                "room_name": "Test Meeting Room",
                "capacity": 10,
                "is_active": 1,
                "description": "Test room for unit tests",
            }
        )
        room.insert()
        self.assertEqual(room.name, "Test Meeting Room")
        self.assertEqual(room.is_active, 1)
        frappe.db.delete("Meeting Room", {"name": "Test Meeting Room"})

    def test_duplicate_room_name(self):
        frappe.get_doc(
            {
                "doctype": "Meeting Room",
                "room_name": "Duplicate Test Room",
                "capacity": 10,
            }
        ).insert()

        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc(
                {
                    "doctype": "Meeting Room",
                    "room_name": "Duplicate Test Room",
                    "capacity": 10,
                }
            ).insert()

        frappe.db.delete("Meeting Room", {"room_name": "Duplicate Test Room"})

    def test_inactive_room_hidden_from_list(self):
        room = frappe.get_doc(
            {
                "doctype": "Meeting Room",
                "room_name": "Inactive Test Room",
                "capacity": 10,
                "is_active": 0,
            }
        )
        room.insert()
        rooms = frappe.get_all(
            "Meeting Room", filters={"is_active": 1}, fields=["name"]
        )
        room_names = [r.name for r in rooms]
        self.assertNotIn("Inactive Test Room", room_names)
        frappe.db.delete("Meeting Room", {"name": "Inactive Test Room"})

    def test_capacity_validation(self):
        room = frappe.get_doc(
            {
                "doctype": "Meeting Room",
                "room_name": "Capacity Test Room",
                "capacity": 5,
            }
        )
        room.insert()
        self.assertEqual(room.capacity, 5)
        frappe.db.delete("Meeting Room", {"name": "Capacity Test Room"})


if __name__ == "__main__":
    unittest.main()