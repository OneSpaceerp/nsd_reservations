app_name = "nsd_reservations"
app_title = "NSD Reservations"
app_publisher = "Nest Software Development"
app_description = "Meeting Room Reservation Module for ERPNext"
app_email = "info@nsd-eg.com"
app_license = "MIT"
app_version = "1.0.0"

has_web_view = 0

required_apps = []

docevents = {
    "Room Reservation": {
        "on_update": "nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.validate_reservation",
        "before_insert": "nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.set_default_fields",
    }
}