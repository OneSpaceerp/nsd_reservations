import calendar
import datetime

import frappe
from frappe.model.document import Document
from frappe.utils import get_fullname, get_url, now_datetime


class RoomReservation(Document):
    def validate(self):
        self._capture_old_workflow_state()
        self.validate_time()
        self.validate_active_room()
        self.validate_capacity()
        self.validate_overlap()

    def _capture_old_workflow_state(self):
        if not self.is_new():
            self._old_workflow_state = frappe.db.get_value(
                "Room Reservation", self.name, "workflow_state"
            )
        else:
            self._old_workflow_state = None

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
                frappe.throw(
                    f"Attendees ({self.number_of_attendees}) exceed room capacity ({room.capacity})"
                )

    def validate_overlap(self):
        if self.meeting_room and self.start_time and self.end_time:
            overlapping = frappe.db.get_all(
                "Room Reservation",
                filters={
                    "meeting_room": self.meeting_room,
                    "docstatus": 1,
                    "start_time": ["<", self.end_time],
                    "end_time": [">", self.start_time],
                    "name": ["!=", self.name or ""],
                },
            )
            if overlapping:
                frappe.throw(
                    f"Overlaps with approved reservation(s): {', '.join(r.name for r in overlapping)}"
                )

    # ── workflow state transitions ────────────────────────────────────────────

    def on_update(self):
        old = getattr(self, "_old_workflow_state", None)
        if old is not None and old != self.workflow_state:
            if self.workflow_state == "Pending Manager Approval":
                self._notify_managers()

    def on_submit(self):
        # Fires when docstatus → 1  (workflow action: Approve → Reserved)
        self.approved_by = frappe.session.user
        self.approved_on = now_datetime()
        self.status = "Reserved"
        self._notify_requester("approved")

    def on_cancel(self):
        # Fires when docstatus → 2  (Reject → Rejected  OR  Cancel → Cancelled)
        if self.workflow_state == "Rejected":
            if not self.rejection_reason:
                frappe.throw(
                    "Rejection Reason is required. Please provide a reason before rejecting."
                )
            self.status = "Rejected"
            self._notify_requester("rejected")
        else:
            self.status = "Cancelled"
            self._notify_requester("cancelled")

    # ── email helpers ────────────────────────────────────────────────────────

    def _notify_managers(self):
        rows = frappe.db.get_all(
            "Has Role",
            filters={"role": "Meeting Room Manager", "parenttype": "User"},
            fields=["parent"],
        )
        recipients = [r.parent for r in rows if r.parent not in ("Guest", "Administrator")]
        if not recipients:
            return
        frappe.sendmail(
            recipients=recipients,
            subject=f"[Room Reservation] Pending Approval: {self.name}",
            message=self._pending_email_body(),
            now=True,
        )

    def _notify_requester(self, action):
        if not self.person_in_charge or self.person_in_charge in ("Guest", "Administrator"):
            return
        labels = {"approved": "Approved ✓", "rejected": "Rejected ✗", "cancelled": "Cancelled"}
        frappe.sendmail(
            recipients=[self.person_in_charge],
            subject=f"[Room Reservation] {labels.get(action, action.title())}: {self.name}",
            message=self._status_email_body(action),
            now=True,
        )

    def _pending_email_body(self):
        link = f"{get_url()}/app/room-reservation/{self.name}"
        return f"""
        <p>A room reservation is awaiting your approval:</p>
        <table cellpadding="6" cellspacing="0" border="1" style="border-collapse:collapse;font-size:13px">
            <tr><td><b>Reservation</b></td><td>{self.name}</td></tr>
            <tr><td><b>Room</b></td><td>{self.meeting_room}</td></tr>
            <tr><td><b>Requested by</b></td><td>{get_fullname(self.person_in_charge)}</td></tr>
            <tr><td><b>Department</b></td><td>{self.department or "-"}</td></tr>
            <tr><td><b>Start</b></td><td>{self.start_time}</td></tr>
            <tr><td><b>End</b></td><td>{self.end_time}</td></tr>
            <tr><td><b>Reason</b></td><td>{self.meeting_reason or "-"}</td></tr>
        </table>
        <p style="margin-top:16px">
            <a href="{link}" style="padding:8px 18px;background:#5b7af0;color:#fff;
               text-decoration:none;border-radius:4px;font-size:13px">Review Reservation</a>
        </p>
        """

    def _status_email_body(self, action):
        link = f"{get_url()}/app/room-reservation/{self.name}"
        colors = {"approved": "#166534", "rejected": "#991b1b", "cancelled": "#6b7280"}
        color = colors.get(action, "#333")
        body = f"""
        <p>Your room reservation <b>{self.name}</b> has been
        <span style="color:{color};font-weight:700">{action.upper()}</span>.</p>
        <table cellpadding="6" cellspacing="0" border="1" style="border-collapse:collapse;font-size:13px">
            <tr><td><b>Room</b></td><td>{self.meeting_room}</td></tr>
            <tr><td><b>Start</b></td><td>{self.start_time}</td></tr>
            <tr><td><b>End</b></td><td>{self.end_time}</td></tr>
        </table>
        """
        if action == "rejected" and self.rejection_reason:
            body += f"<p><b>Reason:</b> {self.rejection_reason}</p>"
        body += f"""
        <p style="margin-top:16px">
            <a href="{link}" style="padding:8px 18px;background:#5b7af0;color:#fff;
               text-decoration:none;border-radius:4px;font-size:13px">View Reservation</a>
        </p>
        """
        return body


# ── whitelisted API for the Roster page ──────────────────────────────────────

@frappe.whitelist()
def get_month_reservations(year, month):
    year  = int(year)
    month = int(month)

    _, days_in_month = calendar.monthrange(year, month)
    start = datetime.date(year, month, 1).strftime("%Y-%m-%d")
    end   = (
        datetime.date(year, month, days_in_month) + datetime.timedelta(days=1)
    ).strftime("%Y-%m-%d")

    reservations = frappe.db.get_all(
        "Room Reservation",
        filters=[
            ["start_time", ">=", start],
            ["start_time", "<",  end],
        ],
        fields=[
            "name", "meeting_room", "start_time", "end_time",
            "workflow_state", "reservation_title",
            "person_in_charge", "department", "number_of_attendees", "company",
        ],
    )

    rooms = frappe.db.get_all(
        "Meeting Room",
        filters={"is_active": 1},
        fields=["name", "room_name", "capacity", "location"],
        order_by="sort_order asc, room_name asc",
    )

    holidays = _get_month_holidays(year, month, start, end)

    return {"rooms": rooms, "reservations": reservations, "holidays": holidays}


def _get_month_holidays(year, month, start, end):
    """Return holidays for the month from the default company's holiday list."""
    try:
        default_company = frappe.db.get_single_value("Global Defaults", "default_company")
        if not default_company:
            return []

        holiday_list = frappe.db.get_value("Company", default_company, "default_holiday_list")
        if not holiday_list:
            return []

        rows = frappe.db.get_all(
            "Holiday",
            filters={
                "parent":       holiday_list,
                "holiday_date": ["between", [start, end]],
            },
            fields=["holiday_date", "description"],
        )

        result = []
        for r in rows:
            hdate = r.holiday_date
            # holiday_date may be a date object or a string depending on Frappe version
            date_str = hdate.strftime("%Y-%m-%d") if hasattr(hdate, "strftime") else str(hdate)
            result.append({"date": date_str, "description": r.description or ""})
        return result

    except Exception:
        # Never break the calendar just because holidays couldn't be fetched
        return []
