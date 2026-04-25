frappe.pages['meeting-roster'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Meeting Roster'),
		single_column: true,
	});
	new MeetingRoster(page, wrapper);
};

frappe.pages['meeting-roster'].on_page_show = function (wrapper) {
	if (wrapper._roster) wrapper._roster.refresh();
};

class MeetingRoster {
	constructor(page, wrapper) {
		this.page = page;
		this.$wrapper = $(wrapper);
		this.current_month = moment();
		this.all_rooms = [];
		this.all_reservations = [];
		this.holidays = [];
		wrapper._roster = this;

		this._make();
		this.load();
	}

	// ── layout ────────────────────────────────────────────────────────────────

	_make() {
		this.page.set_primary_action(__('Create'), () => frappe.new_doc('Room Reservation'), 'add');

		const $main = this.$wrapper.find('.layout-main-section');
		$main.css('padding', 0);

		this.$body = $('<div class="mr-body">').appendTo($main);
		this._make_control_bar();
		this._make_grid_area();
	}

	_make_control_bar() {
		const $bar = $('<div class="mr-control-bar">').appendTo(this.$body);

		const $nav = $('<div class="mr-nav">').appendTo($bar);
		$('<button class="btn btn-xs btn-default mr-nav-btn">‹</button>')
			.appendTo($nav)
			.on('click', () => { this.current_month.subtract(1, 'month'); this.load(); });
		this.$month_lbl = $('<span class="mr-month-label">').appendTo($nav);
		$('<button class="btn btn-xs btn-default mr-nav-btn">›</button>')
			.appendTo($nav)
			.on('click', () => { this.current_month.add(1, 'month'); this.load(); });

		this._company_ctrl = this._add_filter($bar, 'Link',   'company',    'Company',    'Company');
		this._dept_ctrl    = this._add_filter($bar, 'Link',   'department', 'Department', 'Department');
		this._status_ctrl  = this._add_filter($bar, 'Select', 'status',     'Status',
			'\nDraft\nPending Manager Approval\nReserved\nRejected\nCancelled');

		$('<button class="btn btn-xs btn-default mr-clear-btn" title="' + __('Clear filters') + '">✕</button>')
			.appendTo($bar)
			.on('click', () => this._clear_filters());
	}

	_add_filter($parent, fieldtype, fieldname, label, options) {
		const $wrap = $('<div class="mr-filter-item">').appendTo($parent);
		const ctrl = frappe.ui.form.make_control({
			df: {
				fieldtype, fieldname,
				label: __(label), options,
				placeholder: __(label),
				onchange: () => this._render(),
			},
			parent: $wrap[0],
			render_input: true,
		});
		ctrl.$wrapper.find('label').hide();
		ctrl.$wrapper.find('.form-group').css('margin-bottom', 0);
		return ctrl;
	}

	_make_grid_area() {
		const $grid = $('<div class="mr-grid-area">').appendTo(this.$body);
		this.$scroll = $('<div class="mr-scroll">').appendTo($grid);
		this.$table  = $('<table class="mr-table">').appendTo(this.$scroll);
		this.$thead  = $('<thead>').appendTo(this.$table);
		this.$tbody  = $('<tbody>').appendTo(this.$table);
	}

	// ── data ─────────────────────────────────────────────────────────────────

	load() {
		this._update_month_label();
		frappe.call({
			method: 'nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.get_month_reservations',
			args: {
				year:  this.current_month.year(),
				month: this.current_month.month() + 1,
			},
			callback: r => {
				if (r.message) {
					this.all_rooms        = r.message.rooms        || [];
					this.all_reservations = r.message.reservations || [];
					this.holidays         = r.message.holidays     || [];
					this._render();
				}
			},
		});
	}

	refresh() { this.load(); }

	_update_month_label() {
		if (this.$month_lbl) this.$month_lbl.text(this.current_month.format('MMMM, YYYY'));
	}

	// ── render ────────────────────────────────────────────────────────────────

	_render() {
		this._update_month_label();

		const year  = this.current_month.year();
		const month = this.current_month.month();   // 0-based
		const days  = this.current_month.daysInMonth();

		// Holiday set: day-of-month numbers that are holidays
		const holiday_map = {};   // day → description
		for (const h of this.holidays) {
			const hd = moment(h.date);
			if (hd.year() === year && hd.month() === month) {
				holiday_map[hd.date()] = h.description || __('Holiday');
			}
		}

		// Room search
		const search = (this.$search_inp ? this.$search_inp.val() : '').toLowerCase().trim();
		const rooms = this.all_rooms.filter(r =>
			!search || r.room_name.toLowerCase().includes(search)
		);

		// Reservation filters
		const f_co  = this._company_ctrl && this._company_ctrl.get_value();
		const f_dep = this._dept_ctrl    && this._dept_ctrl.get_value();
		const f_st  = this._status_ctrl  && this._status_ctrl.get_value();

		const reservations = this.all_reservations.filter(r => {
			if (f_co  && r.company        !== f_co)  return false;
			if (f_dep && r.department     !== f_dep) return false;
			if (f_st  && r.workflow_state !== f_st)  return false;
			return true;
		});

		// Lookup: "meeting_room|day" → [reservations]
		const lookup = {};
		for (const res of reservations) {
			const d = moment(res.start_time);
			if (d.year() !== year || d.month() !== month) continue;
			const key = `${res.meeting_room}|${d.date()}`;
			(lookup[key] = lookup[key] || []).push(res);
		}

		const DAY_ABBR = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

		// ── header ──────────────────────────────────────────────────────────
		this.$thead.empty();
		const $hr = $('<tr>').appendTo(this.$thead);

		const $corner = $('<th class="mr-th-room">').appendTo($hr);
		this.$search_inp = $('<input type="text" class="form-control mr-room-search" placeholder="' + __('Search Room') + '">')
			.appendTo($corner).val(search)
			.on('input', () => this._render());

		for (let d = 1; d <= days; d++) {
			const date    = moment({ year, month, date: d });
			const today   = date.isSame(moment(), 'day');
			const weekend = [0, 6].includes(date.day());
			const holiday = holiday_map[d];
			const cls = ['mr-th-day',
				today   ? 'is-today'   : '',
				weekend ? 'is-weekend' : '',
				holiday ? 'is-holiday' : '',
			].filter(Boolean).join(' ');

			const $th = $(`<th class="${cls}" title="${holiday || ''}">
				<span class="mr-day-abbr">${DAY_ABBR[date.day()]}</span>
				<span class="mr-day-num">${String(d).padStart(2, '0')}</span>
				${holiday ? '<span class="mr-holiday-dot" title="' + frappe.utils.escape_html(holiday) + '"></span>' : ''}
			</th>`).appendTo($hr);
		}

		// ── body ────────────────────────────────────────────────────────────
		this.$tbody.empty();

		if (!rooms.length) {
			$(`<tr><td colspan="${days + 1}" class="mr-empty">${__('No rooms found')}</td></tr>`)
				.appendTo(this.$tbody);
			return;
		}

		for (const room of rooms) {
			const $tr = $('<tr>').appendTo(this.$tbody);

			// Room cell (sticky left)
			const initial = (room.room_name || '?').charAt(0).toUpperCase();
			$(`<td class="mr-td-room">
				<div class="mr-room-row">
					<div class="mr-avatar">${initial}</div>
					<div class="mr-room-info">
						<div class="mr-room-name">${frappe.utils.escape_html(room.room_name)}</div>
						${room.location ? `<div class="mr-room-sub">${frappe.utils.escape_html(room.location)}</div>` : ''}
					</div>
				</div>
			</td>`).appendTo($tr);

			// Day cells
			for (let d = 1; d <= days; d++) {
				const date    = moment({ year, month, date: d });
				const today   = date.isSame(moment(), 'day');
				const weekend = [0, 6].includes(date.day());
				const holiday = !!holiday_map[d];
				const key     = `${room.name}|${d}`;
				const chips   = lookup[key] || [];

				const cls = ['mr-td-day',
					today   ? 'is-today'   : '',
					weekend ? 'is-weekend' : '',
					holiday ? 'is-holiday' : '',
				].filter(Boolean).join(' ');

				const $td = $(`<td class="${cls}">`).appendTo($tr);

				// Reservation chips
				for (const res of chips) {
					const clr   = this._status_color(res.workflow_state);
					const t1    = moment(res.start_time).format('HH:mm');
					const t2    = moment(res.end_time).format('HH:mm');
					const label = res.reservation_title || res.meeting_room || res.name;

					$(`<div class="mr-chip" style="background:${clr.bg};color:${clr.fg};border-left-color:${clr.fg};">
						<div class="mr-chip-title">${frappe.utils.escape_html(label)}</div>
						<div class="mr-chip-time">${t1}–${t2}</div>
					</div>`)
						.appendTo($td)
						.attr('title', `${label}\n${t1}–${t2}\n${res.workflow_state}`)
						.on('click', e => {
							e.stopPropagation();
							frappe.set_route('Form', 'Room Reservation', res.name);
						});
				}

				// "+" add button — shows on hover
				$('<div class="mr-add-btn" title="' + __('New Reservation') + '">+</div>')
					.appendTo($td)
					.on('click', e => {
						e.stopPropagation();
						this._show_new_dialog(room, date);
					});

				// Click anywhere on empty cell space also opens dialog
				$td.on('click', e => {
					if ($(e.target).closest('.mr-chip, .mr-add-btn').length) return;
					this._show_new_dialog(room, date);
				});
			}
		}
	}

	// ── new reservation dialog ────────────────────────────────────────────────

	_show_new_dialog(room, date) {
		const start_dt = date.format('YYYY-MM-DD') + ' 09:00:00';
		const end_dt   = date.format('YYYY-MM-DD') + ' 10:00:00';

		const d = new frappe.ui.Dialog({
			title: __('New Room Reservation'),
			fields: [
				// Section header: room + date info (read-only context)
				{
					fieldtype: 'Section Break',
					label: `<span style="font-weight:600">${frappe.utils.escape_html(room.room_name)}</span>`
						+ ` &nbsp;·&nbsp; ${date.format('dddd, DD MMMM YYYY')}`
						+ (room.capacity ? ` &nbsp;·&nbsp; ${__('Capacity')}: ${room.capacity}` : ''),
				},
				// Row 1: times
				{
					fieldtype: 'Datetime', fieldname: 'start_time',
					label: __('Start Time'), reqd: 1, default: start_dt,
				},
				{ fieldtype: 'Column Break' },
				{
					fieldtype: 'Datetime', fieldname: 'end_time',
					label: __('End Time'), reqd: 1, default: end_dt,
				},
				// Row 2: people
				{ fieldtype: 'Section Break' },
				{
					fieldtype: 'Link', fieldname: 'person_in_charge',
					label: __('Person in Charge'), options: 'User',
					reqd: 1, default: frappe.session.user,
				},
				{ fieldtype: 'Column Break' },
				{
					fieldtype: 'Link', fieldname: 'department',
					label: __('Department'), options: 'Department', reqd: 1,
				},
				// Row 3: attendees + title
				{ fieldtype: 'Section Break' },
				{
					fieldtype: 'Int', fieldname: 'number_of_attendees',
					label: __('Number of Attendees'), reqd: 1, default: 1,
				},
				{ fieldtype: 'Column Break' },
				{
					fieldtype: 'Data', fieldname: 'reservation_title',
					label: __('Reservation Title'),
					description: __('Auto-generated if left blank'),
				},
				// Row 4: reason + notes
				{ fieldtype: 'Section Break' },
				{
					fieldtype: 'Small Text', fieldname: 'meeting_reason',
					label: __('Meeting Reason'), reqd: 1,
				},
				{ fieldtype: 'Column Break' },
				{
					fieldtype: 'Small Text', fieldname: 'notes',
					label: __('Notes'),
				},
			],
			primary_action_label: __('Save'),
			primary_action: (values) => {
				const title = values.reservation_title ||
					`${room.room_name} - ${values.meeting_reason}`;

				frappe.call({
					method: 'nsd_reservations.meeting_management.doctype.room_reservation.room_reservation.create_and_submit_reservation',
					args: {
						doc_data: {
							meeting_room:        room.name,
							reservation_title:   title,
							start_time:          values.start_time,
							end_time:            values.end_time,
							person_in_charge:    values.person_in_charge,
							department:          values.department,
							meeting_reason:      values.meeting_reason,
							number_of_attendees: values.number_of_attendees,
							notes:               values.notes || '',
						},
					},
					freeze: true,
					freeze_message: __('Submitting reservation…'),
					callback: r => {
						if (r.message) {
							d.hide();
							const state = r.message.workflow_state || 'Draft';
							frappe.show_alert({
								message: __('Reservation {0} — {1}', [
									`<b>${r.message.name}</b>`, __(state),
								]),
								indicator: state === 'Pending Manager Approval' ? 'orange' : 'green',
							}, 5);
							this.load();
						}
					},
				});
			},
		});

		d.show();
	}

	// ── helpers ───────────────────────────────────────────────────────────────

	_status_color(state) {
		return {
			'Draft':                    { bg: '#fef9c3', fg: '#92400e' },
			'Pending Manager Approval': { bg: '#ffedd5', fg: '#c2410c' },
			'Reserved':                 { bg: '#dcfce7', fg: '#166534' },
			'Rejected':                 { bg: '#fee2e2', fg: '#991b1b' },
			'Cancelled':                { bg: '#f3f4f6', fg: '#6b7280' },
		}[state] || { bg: '#eff6ff', fg: '#1d4ed8' };
	}

	_clear_filters() {
		[this._company_ctrl, this._dept_ctrl, this._status_ctrl].forEach(c => c && c.set_value(''));
		this._render();
	}
}
