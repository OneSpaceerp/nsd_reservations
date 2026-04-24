frappe.ui.form.on("Meeting Room", {
    refresh: function (frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("View Reservations"), function () {
                frappe.set_route("List", "Room Reservation", {
                    meeting_room: frm.doc.name,
                });
            });
        }
    },
    is_active: function (frm) {
        if (!frm.doc.is_active && !frm.is_new()) {
            frappe.call({
                method:
                    "nsd_reservations.meeting_management.doctype.meeting_room.meeting_room.check_active_reservations",
                args: {
                    room_name: frm.doc.name,
                },
                callback: function (r) {
                    if (r.message > 0) {
                        frappe.msgprint(
                            __(
                                "This room has {0} active reservation(s). Deactivating will hide it from new reservations."
                            ).format(r.message),
                            __("Warning"),
                            "warning"
                        );
                    }
                },
            });
        }
    },
});