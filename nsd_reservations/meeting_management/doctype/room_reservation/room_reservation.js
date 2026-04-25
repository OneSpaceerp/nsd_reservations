frappe.ui.form.on('Room Reservation', {

	refresh(frm) {
		frm.trigger('set_status_indicator');
		frm.trigger('show_room_info');
		frm.trigger('add_action_buttons');
		frm.trigger('auto_set_title');
	},

	// ── status badge ────────────────────────────────────────────────────────

	set_status_indicator(frm) {
		const COLOR = {
			'Draft':                    'yellow',
			'Pending Manager Approval': 'orange',
			'Reserved':                 'green',
			'Rejected':                 'red',
			'Cancelled':                'grey',
		};
		const state = frm.doc.workflow_state || frm.doc.status;
		if (state && COLOR[state]) frm.set_indicator(state, COLOR[state]);
	},

	// ── room info intro ─────────────────────────────────────────────────────

	show_room_info(frm) {
		if (!frm.doc.meeting_room) return;
		frappe.db.get_value('Meeting Room', frm.doc.meeting_room, ['capacity', 'location'], r => {
			const parts = [];
			if (r && r.capacity) parts.push(`${__('Capacity')}: ${r.capacity}`);
			if (r && r.location) parts.push(`${__('Location')}: ${r.location}`);
			if (parts.length) frm.set_intro(parts.join('  |  '), 'blue');
		});
	},

	// ── custom action buttons ───────────────────────────────────────────────

	add_action_buttons(frm) {
		const is_manager = frappe.user.has_role(['Meeting Room Manager', 'System Manager']);
		const state = frm.doc.workflow_state;

		if (is_manager && state === 'Pending Manager Approval' && !frm.is_dirty()) {
			frm.add_custom_button(__('Approve'), () => {
				frappe.confirm(
					__('Approve reservation for <b>{0}</b>?', [frm.doc.meeting_room]),
					() => _apply_workflow(frm, 'Approve')
				);
			}).addClass('btn-success');

			frm.add_custom_button(__('Reject'), () => _show_reject_dialog(frm))
				.addClass('btn-danger');
		}

		frm.add_custom_button(__('Meeting Roster'), () => frappe.set_route('meeting-roster'), __('View'));
	},

	// ── field triggers ──────────────────────────────────────────────────────

	meeting_room(frm) {
		frm.trigger('show_room_info');
		frm.trigger('auto_set_title');
	},

	meeting_reason(frm) {
		frm.trigger('auto_set_title');
	},

	auto_set_title(frm) {
		if (frm.is_new() && !frm.doc.reservation_title && frm.doc.meeting_room) {
			frm.set_value(
				'reservation_title',
				`${frm.doc.meeting_room} - ${frm.doc.meeting_reason || __('Meeting')}`
			);
		}
	},

	// ── intercept native workflow "Reject" button ───────────────────────────

	before_workflow_action(frm) {
		if (frm.selected_workflow_action === 'Reject') {
			return new Promise((resolve, reject) => {
				const d = new frappe.ui.Dialog({
					title: __('Reject Reservation'),
					fields: [{
						fieldtype: 'Small Text',
						fieldname: 'rejection_reason',
						label: __('Rejection Reason'),
						reqd: 1,
						description: __('Provide a clear reason. This will be sent to the requester.'),
					}],
					primary_action_label: __('Confirm Rejection'),
					primary_action(vals) {
						frm.doc.rejection_reason = vals.rejection_reason;
						d.hide();
						resolve();
					},
					secondary_action_label: __('Cancel'),
					secondary_action() {
						d.hide();
						reject();
					},
				});
				d.show();
			});
		}
	},
});

// ── module-level helpers (not part of the form event object) ─────────────────

function _apply_workflow(frm, action) {
	return frappe.call({
		method: 'frappe.model.workflow.apply_workflow',
		args: { doc: frm.doc, action },
		callback(r) {
			if (r.message) {
				frappe.model.sync(r.message);
				frm.refresh();
			}
		},
	});
}

function _show_reject_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Reject Reservation'),
		fields: [{
			fieldtype: 'Small Text',
			fieldname: 'rejection_reason',
			label: __('Rejection Reason'),
			reqd: 1,
			description: __('Provide a clear reason. This will be sent to the requester.'),
		}],
		primary_action_label: __('Reject'),
		primary_action(vals) {
			frm.set_value('rejection_reason', vals.rejection_reason);
			d.hide();
			_apply_workflow(frm, 'Reject');
		},
	});
	d.show();
}
