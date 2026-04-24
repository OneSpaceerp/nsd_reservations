frappe.ui.form.on("Room Reservation", {
    refresh: function (frm) {
        frm.trigger("set_default_values");
        frm.trigger("setup_workflow_buttons");
        frm.trigger("setup_calendar_link");
        frm.trigger("update_status_badge");
    },

    set_default_values: function (frm) {
        if (frm.is_new()) {
            if (!frm.doc.person_in_charge) {
                frm.set_value("person_in_charge", frappe.session.user);
            }
            if (!frm.doc.source) {
                frm.set_value("source", "Form");
            }
        }
    },

    setup_workflow_buttons: function (frm) {
        if (frm.doc.workflow_state === "Draft") {
            frm.add_custom_button(__("Submit for Approval"), function () {
                frm.set_value("workflow_state", "Pending Manager Approval");
                frm.save();
            }).addClass("btn-primary");
        }

        if (
            frm.doc.workflow_state === "Pending Manager Approval" &&
            frm.is_edit_mode()
        ) {
            if (
                frappe.user.has_role("Meeting Room Manager") ||
                frappe.user.has_role("System Manager")
            ) {
                frm.add_custom_button(__("Approve"), function () {
                    approve_reservation(frm);
                }).addClass("btn-success");

                frm.add_custom_button(__("Reject"), function () {
                    show_rejection_dialog(frm);
                }).addClass("btn-danger");
            }
        }

        if (
            frm.doc.workflow_state === "Reserved" &&
            (frappe.user.has_role("Meeting Room Manager") ||
                frappe.user.has_role("System Manager"))
        ) {
            frm.add_custom_button(__("Cancel Reservation"), function () {
                cancel_reservation(frm);
            }).addClass("btn-warning");
        }
    },

    setup_calendar_link: function (frm) {
        if (!frm.is_new() && frm.doc.name) {
            frm.add_custom_button(__("View in Calendar"), function () {
                frappe.set_route("List", "Room Reservation", {
                    meeting_room: frm.doc.meeting_room,
                    start_time: ["between", [frm.doc.start_time, frm.doc.end_time]],
                });
            });
        }
    },

    update_status_badge: function (frm) {
        if (frm.doc.workflow_state) {
            var colors = {
                "Draft": "orange",
                "Pending Manager Approval": "yellow",
                "Reserved": "green",
                "Rejected": "red",
                "Cancelled": "grey",
            };
            var color = colors[frm.doc.workflow_state] || "blue";
            frm.set_value("status", frm.doc.workflow_state);
        }
    },

    meeting_room: function (frm) {
        if (frm.doc.meeting_room) {
            frm.trigger("check_room_availability");
            load_room_details(frm);
        }
    },

    start_time: function (frm) {
        if (frm.doc.meeting_room && frm.doc.start_time && frm.doc.end_time) {
            frm.trigger("check_room_availability");
        }
    },

    end_time: function (frm) {
        if (frm.doc.meeting_room && frm.doc.start_time && frm.doc.end_time) {
            frm.trigger("check_room_availability");
        }
    },

    check_room_availability: function (frm) {
        if (
            !frm.doc.meeting_room ||
            !frm.doc.start_time ||
            !frm.doc.end_time
        ) {
            return;
        }

        frm.call({
            method:
                "nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.check_room_availability",
            args: {
                room: frm.doc.meeting_room,
                start_time: frm.doc.start_time,
                end_time: frm.doc.end_time,
                exclude_reservation: frm.doc.name,
            },
            callback: function (r) {
                if (r.message) {
                    if (!r.message.available) {
                        frappe.msgprint(
                            r.message.message,
                            __("Booking Conflict"),
                            "error"
                        );
                        frm.set_value("is_conflict", 1);
                    } else {
                        frm.set_value("is_conflict", 0);
                    }
                }
            },
        });
    },
});

function load_room_details(frm) {
    frappe.call({
        method:
            "nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.get_rooms_for_reservation",
        callback: function (r) {
            if (r.message) {
                var rooms = r.message;
                var selected_room = rooms.find(function (room) {
                    return room.name === frm.doc.meeting_room;
                });

                if (selected_room && selected_room.capacity) {
                    frm.set_df_property(
                        "number_of_attendees",
                        "description",
                        "Room capacity: " + selected_room.capacity
                    );
                }
            }
        },
    });
}

function approve_reservation(frm) {
    frappe.call({
        method:
            "nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.approve_reservation",
        args: {
            reservation_id: frm.doc.name,
        },
        callback: function (r) {
            if (!r.exc) {
                frappe.msgprint(
                    __("Reservation approved successfully"),
                    __("Success"),
                    "success"
                );
                frm.reload_doc();
            }
        },
    });
}

function show_rejection_dialog(frm) {
    var dialog = new frappe.ui.Dialog({
        title: __("Reject Reservation"),
        fields: [
            {
                fieldtype: "Small Text",
                fieldname: "rejection_reason",
                label: __("Rejection Reason"),
                reqd: 1,
            },
        ],
        primary_action_label: __("Reject"),
        primary_action: function () {
            var values = dialog.get_values();
            if (values.rejection_reason) {
                dialog.hide();
                reject_reservation(frm, values.rejection_reason);
            }
        },
    });
    dialog.show();
}

function reject_reservation(frm, reason) {
    frappe.call({
        method:
            "nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.reject_reservation",
        args: {
            reservation_id: frm.doc.name,
            rejection_reason: reason,
        },
        callback: function (r) {
            if (!r.exc) {
                frappe.msgprint(
                    __("Reservation rejected"),
                    __("Success"),
                    "success"
                );
                frm.reload_doc();
            }
        },
    });
}

function cancel_reservation(frm) {
    frappe.confirm(
        __("Are you sure you want to cancel this reservation?"),
        function () {
            frappe.call({
                method:
                    "nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.cancel_reservation",
                args: {
                    reservation_id: frm.doc.name,
                },
                callback: function (r) {
                    if (!r.exc) {
                        frappe.msgprint(
                            __("Reservation cancelled successfully"),
                            __("Success"),
                            "success"
                        );
                        frm.reload_doc();
                    }
                },
            });
        }
    );
}