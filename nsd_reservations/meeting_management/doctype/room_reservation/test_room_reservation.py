import frappe
import unittest
from frappe.utils import add_days, add_hours, now_datetime, today
from datetime import datetime, timedelta
import time


class TestRoomReservation(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")

        self.test_room = frappe.get_doc(
            {
                "doctype": "Meeting Room",
                "room_name": "Test Meeting Room_" + str(int(time.time())),
                "capacity": 10,
                "is_active": 1,
            }
        )
        self.test_room.insert()

    def tearDown(self):
        if self.test_room and self.test_room.name:
            frappe.db.delete("Room Reservation", {"meeting_room": self.test_room.name})
            frappe.db.delete("Meeting Room", {"name": self.test_room.name})

    def test_create_reservation(self):
        start = add_hours(now_datetime(), 2)
        end = add_hours(start, 1)

        reservation = frappe.get_doc(
            {
                "doctype": "Room Reservation",
                "meeting_room": self.test_room.name,
                "start_time": start,
                "end_time": end,
                "person_in_charge": frappe.session.user,
                "department": "Accounts",
                "meeting_reason": "Test meeting",
                "number_of_attendees": 5,
                "workflow_state": "Draft",
            }
        )
        reservation.insert()
        self.assertEqual(reservation.workflow_state, "Draft")
        frappe.db.delete("Room Reservation", {"name": reservation.name})

    def test_time_validation(self):
        start = add_hours(now_datetime(), 2)
        end = add_hours(start, -1)

        reservation = frappe.get_doc(
            {
                "doctype": "Room Reservation",
                "meeting_room": self.test_room.name,
                "start_time": end,
                "end_time": start,
                "person_in_charge": frappe.session.user,
                "department": "Accounts",
                "meeting_reason": "Test meeting",
                "number_of_attendees": 5,
            }
        )

        with self.assertRaises(frappe.ValidationError):
            reservation.insert()

    def test_capacity_validation(self):
        start = add_hours(now_datetime(), 2)
        end = add_hours(start, 1)

        reservation = frappe.get_doc(
            {
                "doctype": "Room Reservation",
                "meeting_room": self.test_room.name,
                "start_time": start,
                "end_time": end,
                "person_in_charge": frappe.session.user,
                "department": "Accounts",
                "meeting_reason": "Test meeting",
                "number_of_attendees": 15,
            }
        )

        with self.assertRaises(frappe.ValidationError):
            reservation.insert()

    def test_overlap_detection(self):
        start1 = add_hours(now_datetime(), 2)
        end1 = add_hours(start1, 1)

        reservation1 = frappe.get_doc(
            {
                "doctype": "Room Reservation",
                "meeting_room": self.test_room.name,
                "start_time": start1,
                "end_time": end1,
                "person_in_charge": frappe.session.user,
                "department": "Accounts",
                "meeting_reason": "First meeting",
                "number_of_attendees": 5,
                "workflow_state": "Reserved",
                "docstatus": 1,
            }
        )
        reservation1.insert()
        frappe.db.set_value("Room Reservation", reservation1.name, "workflow_state", "Reserved")
        frappe.db.set_value("Room Reservation", reservation1.name, "docstatus", 1)

        start2 = add_hours(now_datetime(), 2)
        end2 = add_hours(start2, 1)

        reservation2 = frappe.get_doc(
            {
                "doctype": "Room Reservation",
                "meeting_room": self.test_room.name,
                "start_time": start2,
                "end_time": end2,
                "person_in_charge": frappe.session.user,
                "department": "Accounts",
                "meeting_reason": "Conflicting meeting",
                "number_of_attendees": 5,
            }
        )

        with self.assertRaises(frappe.ValidationError):
            reservation2.insert()

        frappe.db.delete("Room Reservation", {"name": reservation1.name})


if __name__ == "__main__":
    unittest.main()