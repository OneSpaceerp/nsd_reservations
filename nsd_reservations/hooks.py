app_name = "nsd_reservations"
app_title = "NSD Reservations"
app_publisher = "NSD"
app_description = "Meeting Room Reservation Module for ERPNext v16"
app_version = "1.0.0"
app_icon = "fa fa-calendar"
app_color = "blue"
module = "Meeting Management"

modules = [
    {
        "module_name": "Meeting Management",
        "color": "blue",
        "icon": "fa fa-calendar",
    }
]

doc_events = {}

doctype_js = {
    "Room Reservation": "public/js/room_reservation.js",
    "Meeting Room": "public/js/meeting_room.js",
}

fixtures = ["Role", "Workflow", "Report", "Workspace", "Dashboard Chart", "Number Card"]
scheduler_events = {}
