import frappe
import frappe.utils
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import getdate, today, now_datetime, add_days


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Reservation ID"),
            "fieldtype": "Link",
            "options": "Room Reservation",
            "width": 120,
        },
        {
            "fieldname": "meeting_room",
            "label": _("Room"),
            "fieldtype": "Link",
            "options": "Meeting Room",
            "width": 150,
        },
        {
            "fieldname": "start_time",
            "label": _("Start Time"),
            "fieldtype": "Datetime",
            "width": 150,
        },
        {
            "fieldname": "end_time",
            "label": _("End Time"),
            "fieldtype": "Datetime",
            "width": 150,
        },
        {
            "fieldname": "duration",
            "label": _("Duration (Hours)"),
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "fieldname": "person_in_charge",
            "label": _("Person in Charge"),
            "fieldtype": "Link",
            "options": "User",
            "width": 150,
        },
        {
            "fieldname": "department",
            "label": _("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "width": 120,
        },
        {
            "fieldname": "number_of_attendees",
            "label": _("Attendees"),
            "fieldtype": "Int",
            "width": 80,
        },
        {
            "fieldname": "workflow_state",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 140,
        },
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters.get("meeting_room"):
        conditions.append("rr.meeting_room = %(meeting_room)s")
        values["meeting_room"] = filters["meeting_room"]

    if filters.get("department"):
        conditions.append("rr.department = %(department)s")
        values["department"] = filters["department"]

    if filters.get("workflow_state"):
        conditions.append("rr.workflow_state = %(workflow_state)s")
        values["workflow_state"] = filters["workflow_state"]

    if filters.get("from_date"):
        conditions.append("rr.start_time >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("rr.start_time <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = """
        SELECT
            rr.name,
            rr.meeting_room,
            rr.start_time,
            rr.end_time,
            TIMESTAMPDIFF(MINUTE, rr.start_time, rr.end_time) / 60 as duration,
            rr.person_in_charge,
            rr.department,
            rr.number_of_attendees,
            rr.workflow_state
        FROM `tabRoom Reservation` rr
        WHERE {where_clause}
        ORDER BY rr.start_time DESC
    """.format(where_clause=where_clause)

    data = frappe.db.sql(query, values, as_dict=1)

    return data


def get_report_summary(filters):
    if not filters:
        filters = {}

    report_summary = []

    total = frappe.db.count("Room Reservation", filters)
    report_summary.append(
        {"label": _("Total Reservations"), "value": str(total), "datatype": "Int"}
    )

    pending = frappe.db.count("Room Reservation", {"workflow_state": "Pending Manager Approval"})
    report_summary.append(
        {"label": _("Pending Approvals"), "value": str(pending), "datatype": "Int"}
    )

    approved = frappe.db.count(
        "Room Reservation", {"workflow_state": "Reserved", "docstatus": 1}
    )
    report_summary.append(
        {"label": _("Approved Reservations"), "value": str(approved), "datatype": "Int"}
    )

    rejected = frappe.db.count("Room Reservation", {"workflow_state": "Rejected"})
    report_summary.append(
        {"label": _("Rejected Reservations"), "value": str(rejected), "datatype": "Int"}
    )

    return report_summary