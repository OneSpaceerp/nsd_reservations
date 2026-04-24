frappe.ui.form.on('Meeting Room', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && !frm.doc.is_active) {
            frm.set_intro("This room is inactive and cannot be reserved", "red");
        }
    }
});
