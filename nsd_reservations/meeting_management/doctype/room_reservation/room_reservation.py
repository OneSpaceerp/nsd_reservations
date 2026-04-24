import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import datetime, get_datetime, now_datetime


class RoomReservation(Document):
    def before_save(self):
        self.set_reservation_title()
        self.validate_time_order()
        self.validate_active_room()
        self.validate_capacity()

    def validate(self):
        self.validate_required_fields()
        self.validate_time_order()
        self.validate_active_room()
        self.validate_capacity()

        if self.is_new() or self.has_value_changed("meeting_room") or self.has_value_changed("start_time") or self.has_value_changed("end_time"):
            self.check_overlap()

    def before_validate(self):
        if not self.workflow_state:
            self.workflow_state = "Draft"

    def set_default_fields(self):
        if not self.person_in_charge:
            self.person_in_charge = frappe.session.user

        if not self.workflow_state:
            self.workflow_state = "Draft"

    def set_reservation_title(self):
        if not self.reservation_title:
            if self.meeting_room and self.start_time:
                room_name = frappe.db.get_value("Meeting Room", self.meeting_room, "room_name")
                self.reservation_title = f"{room_name} - {frappe.utils.format_date(self.start_time, 'dd-MMM-yyyy')} {frappe.utils.format_time(self.start_time, 'HH:mm')}"
            else:
                self.reservation_title = f"Reservation {frappe.utils.now()}"

    def validate_required_fields(self):
        required_fields = ["meeting_room", "start_time", "end_time", "person_in_charge", "department", "meeting_reason", "number_of_attendees"]
        for field in required_fields:
            if not self.get(field):
                frappe.throw(_("{0} is required").format(self.meta.get_label(field)))

    def validate_time_order(self):
        if self.start_time and self.end_time:
            if get_datetime(self.start_time) >= get_datetime(self.end_time):
                frappe.throw(_("End time must be after start time"))

            duration = get_datetime(self.end_time) - get_datetime(self.start_time)
            max_duration = frappe.utils.to_timedelta("4:0:0")
            if duration > max_duration:
                frappe.throw(_("Reservation duration cannot exceed 4 hours"))

    def validate_active_room(self):
        if self.meeting_room:
            room = frappe.get_doc("Meeting Room", self.meeting_room)
            if not room.is_active:
                frappe.throw(_("Meeting room {0} is not active").format(room.room_name))

    def validate_capacity(self):
        if self.meeting_room and self.number_of_attendees:
            room = frappe.get_doc("Meeting Room", self.meeting_room)
            if room.capacity and self.number_of_attendees > room.capacity:
                frappe.throw(
                    _(
                        "Number of attendees ({0}) exceeds room capacity ({1})"
                    ).format(self.number_of_attendees, room.capacity)
                )

    def check_overlap(self):
        if not self.meeting_room or not self.start_time or not self.end_time:
            return

        if self.workflow_state in ["Rejected", "Cancelled"]:
            return

        existing_reservations = frappe.db.sql(
            """
            SELECT name, start_time, end_time, reservation_title, workflow_state
            FROM `tabRoom Reservation`
            WHERE meeting_room = %(room)s
            AND workflow_state = 'Reserved'
            AND docstatus = 1
            AND (
                (start_time < %(end_time)s AND end_time > %(start_time)s)
            )
            {condition}
            """.format(
                condition="AND name != %(name)s" if self.name else ""
            ),
            {
                "room": self.meeting_room,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "name": self.name,
            },
            as_dict=1,
        )

        if existing_reservations:
            conflict = existing_reservations[0]
            frappe.throw(
                _(
                    "This reservation overlaps with an existing reservation '{0}' for the same room from {1} to {2}"
                ).format(
                    conflict.reservation_title,
                    frappe.utils.format_datetime(conflict.start_time, "HH:mm"),
                    frappe.utils.format_datetime(conflict.end_time, "HH:mm"),
                )
            )

    def validate_reservation(self):
        if self.workflow_state == "Reserved":
            self.check_overlap()


@frappe.whitelist()
def check_room_availability(room, start_time, end_time, exclude_reservation=None):
    if not room or not start_time or not end_time:
        return {"available": False, "message": "Missing required parameters"}

    excluded_condition = ""
    if exclude_reservation:
        excluded_condition = "AND name != %(exclude)s"

    overlapping = frappe.db.sql(
        """
        SELECT name, start_time, end_time, reservation_title
        FROM `tabRoom Reservation`
        WHERE meeting_room = %(room)s
        AND workflow_state = 'Reserved'
        AND docstatus = 1
        AND (
            (start_time < %(end_time)s AND end_time > %(start_time)s)
        )
        {condition}
        """.format(
            condition=excluded_condition
        ),
        {
            "room": room,
            "start_time": start_time,
            "end_time": end_time,
            "exclude": exclude_reservation,
        },
        as_dict=1,
    )

    if overlapping:
        return {
            "available": False,
            "message": "Room is not available for the selected time",
            "conflict": overlapping[0],
        }

    return {"available": True, "message": "Room is available"}


@frappe.whitelist()
def get_rooms_for_reservation(only_active=True):
    filters = {}
    if only_active:
        filters["is_active"] = 1

    rooms = frappe.get_all(
        "Meeting Room",
        filters=filters,
        fields=["name", "room_name", "capacity", "location", "description"],
        order_by="sort_order, room_name",
    )
    return rooms


@frappe.whitelist()
def get_room_reservations_for_calendar(room=None, department=None, status=None, from_date=None, to_date=None):
    filters = {"docstatus": ("!=", 2)}

    if room:
        filters["meeting_room"] = room
    if department:
        filters["department"] = department
    if status:
        if status == "Pending":
            filters["workflow_state"] = "Pending Manager Approval"
        elif status == "Approved":
            filters["workflow_state"] = "Reserved"
        elif status == "Rejected":
            filters["workflow_state"] = "Rejected"
        elif status == "Cancelled":
            filters["workflow_state"] = "Cancelled"

    if from_date:
        filters[">=start_time"] = from_date
    if to_date:
        filters["<=start_time"] = to_date

    reservations = frappe.get_all(
        "Room Reservation",
        filters=filters,
        fields=[
            "name",
            "reservation_title",
            "meeting_room",
            "start_time",
            "end_time",
            "workflow_state",
            "person_in_charge",
            "department",
            "meeting_reason",
            "number_of_attendees",
        ],
        order_by="start_time",
    )

    formatted_reservations = []
    for res in reservations:
        color = get_status_color(res.workflow_state)
        formatted_reservations.append(
            {
                "id": res.name,
                "title": res.reservation_title or res.meeting_room,
                "start": res.start_time,
                "end": res.end_time,
                "color": color,
                "meeting_room": res.meeting_room,
                "workflow_state": res.workflow_state,
                "person_in_charge": res.person_in_charge,
                "department": res.department,
                "meeting_reason": res.meeting_reason,
                "number_of_attendees": res.number_of_attendees,
            }
        )

    return formatted_reservations


def get_status_color(status):
    colors = {
        "Draft": "#FFA500",
        "Pending Manager Approval": "#FFD700",
        "Reserved": "#28A745",
        "Rejected": "#DC3545",
        "Cancelled": "#6C757D",
    }
    return colors.get(status, "#17A2B8")


@frappe.whitelist()
def approve_reservation(reservation_id, approver=None):
    if not approver:
        approver = frappe.session.user

    reservation = frappe.get_doc("Room Reservation", reservation_id)

    if reservation.workflow_state != "Pending Manager Approval":
        frappe.throw(_("Only reservations pending approval can be approved"))

    reservation.check_overlap()

    reservation.workflow_state = "Reserved"
    reservation.approved_by = approver
    reservation.approved_on = now_datetime()
    reservation.save()

    frappe.publish_realtime(
        "reservation_approved",
        {"reservation": reservation.name, "room": reservation.meeting_room},
        after_commit=True,
    )

    return reservation


@frappe.whitelist()
def reject_reservation(reservation_id, rejection_reason, approver=None):
    if not approver:
        approver = frappe.session.user

    reservation = frappe.get_doc("Room Reservation", reservation_id)

    if reservation.workflow_state != "Pending Manager Approval":
        frappe.throw(_("Only reservations pending approval can be rejected"))

    reservation.workflow_state = "Rejected"
    reservation.rejection_reason = rejection_reason
    reservation.approved_by = approver
    reservation.approved_on = now_datetime()
    reservation.save()

    frappe.publish_realtime(
        "reservation_rejected",
        {"reservation": reservation.name, "reason": rejection_reason},
        after_commit=True,
    )

    return reservation


@frappe.whitelist()
def cancel_reservation(reservation_id, cancellation_note=None):
    reservation = frappe.get_doc("Room Reservation", reservation_id)

    if reservation.workflow_state not in ["Reserved", "Pending Manager Approval"]:
        frappe.throw(_("Only active or pending reservations can be cancelled"))

    reservation.workflow_state = "Cancelled"
    if cancellation_note:
        reservation.notes = (reservation.notes or "") + "\n" + cancellation_note

    reservation.save()

    frappe.publish_realtime(
        "reservation_cancelled",
        {"reservation": reservation.name},
        after_commit=True,
    )

    return reservation