frappe.ui.form.on('Room Reservation', {
    refresh: function(frm) {
        const color_map = {
            "Draft": "#ffcc00",
            "Pending Manager Approval": "#ff9900",
            "Reserved": "#00cc00",
            "Rejected": "#ff0000",
            "Cancelled": "#999999"
        };
        if (frm.doc.status && color_map[frm.doc.status]) {
            frm.set_df_property("status", "color", color_map[frm.doc.status]);
        }
        if (!frm.doc.reservation_title && frm.doc.meeting_room) {
            frm.set_value("reservation_title", `${frm.doc.meeting_room} - ${frm.doc.meeting_reason || "Meeting"}`);
        }
    },
    meeting_room: function(frm) {
        if (frm.doc.meeting_room) {
            frappe.db.get_value("Meeting Room", frm.doc.meeting_room, "capacity", (r) => {
                if (r.capacity) frm.set_intro(`Room Capacity: ${r.capacity}`, "blue");
            });
        }
    }
});
