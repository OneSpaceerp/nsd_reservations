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
		wrapper._roster = this;

		this._make();
		this.load();
	}

	// ── layout ────────────────────────────────────────────────────────────────

	_make() {
		this.page.set_primary_action(__('Create'), () => frappe.new_doc('Room Reservation'), 'add');

		// Clear the default layout-main content and inject ours
		const $main = this.$wrapper.find('.layout-main-section');
		$main.css('padding', 0);

		this.$body = $('<div class="mr-body">').appendTo($main);

		this._make_control_bar();
		this._make_grid_area();
	}

	_make_control_bar() {
		const $bar = $('<div class="mr-control-bar">').appendTo(this.$body);

		// Month navigation
		const $nav = $('<div class="mr-nav">').appendTo($bar);

		$('<button class="btn btn-xs btn-default mr-nav-btn">‹</button>')
			.appendTo($nav)
			.on('click', () => { this.current_month.subtract(1, 'month'); this.load(); });

		this.$month_lbl = $('<span class="mr-month-label">').appendTo($nav);

		$('<button class="btn btn-xs btn-default mr-nav-btn">›</button>')
			.appendTo($nav)
			.on('click', () => { this.current_month.add(1, 'month'); this.load(); });

		// Filters
		this._company_ctrl = this._add_filter($bar, 'Link', 'company', 'Company', 'Company');
		this._dept_ctrl    = this._add_filter($bar, 'Link', 'department', 'Department', 'Department');
		this._status_ctrl  = this._add_filter($bar, 'Select', 'status', 'Status',
			'\nDraft\nPending Manager Approval\nReserved\nRejected\nCancelled');

		// Clear filters
		$('<button class="btn btn-xs btn-default mr-clear-btn" title="' + __('Clear filters') + '">✕</button>')
			.appendTo($bar)
			.on('click', () => this._clear_filters());
	}

	_add_filter($parent, fieldtype, fieldname, label, options) {
		const $wrap = $('<div class="mr-filter-item">').appendTo($parent);
		const ctrl = frappe.ui.form.make_control({
			df: {
				fieldtype,
				fieldname,
				label: __(label),
				options,
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

		// Left panel: search + sticky room names live inside the table
		// Right panel: horizontally scrollable day grid
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
				year: this.current_month.year(),
				month: this.current_month.month() + 1,
			},
			callback: r => {
				if (r.message) {
					this.all_rooms = r.message.rooms || [];
					this.all_reservations = r.message.reservations || [];
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

		// Apply search filter on rooms
		const search = (this.$search_inp ? this.$search_inp.val() : '').toLowerCase().trim();
		const rooms = this.all_rooms.filter(r =>
			!search || r.room_name.toLowerCase().includes(search)
		);

		// Apply dropdown filters on reservations
		const f_co  = this._company_ctrl && this._company_ctrl.get_value();
		const f_dep = this._dept_ctrl    && this._dept_ctrl.get_value();
		const f_st  = this._status_ctrl  && this._status_ctrl.get_value();

		const reservations = this.all_reservations.filter(r => {
			if (f_co  && r.company       !== f_co)  return false;
			if (f_dep && r.department    !== f_dep) return false;
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

		// ── header row ──────────────────────────────────────────────────────
		this.$thead.empty();
		const $hr = $('<tr>').appendTo(this.$thead);

		// Corner cell: holds the room search input
		const $corner = $('<th class="mr-th-room">').appendTo($hr);
		this.$search_inp = $('<input type="text" class="form-control mr-room-search" placeholder="' + __('Search Room') + '">')
			.appendTo($corner)
			.val(search)
			.on('input', () => this._render());

		for (let d = 1; d <= days; d++) {
			const date    = moment({ year, month, date: d });
			const today   = date.isSame(moment(), 'day');
			const weekend = [0, 6].includes(date.day());
			$(`<th class="mr-th-day${today ? ' is-today' : ''}${weekend ? ' is-weekend' : ''}">
				<span class="mr-day-abbr">${DAY_ABBR[date.day()]}</span>
				<span class="mr-day-num">${String(d).padStart(2, '0')}</span>
			</th>`).appendTo($hr);
		}

		// ── body rows ────────────────────────────────────────────────────────
		this.$tbody.empty();

		if (!rooms.length) {
			$(`<tr><td colspan="${days + 1}" class="mr-empty">${__('No rooms found')}</td></tr>`)
				.appendTo(this.$tbody);
			return;
		}

		for (const room of rooms) {
			const $tr = $('<tr>').appendTo(this.$tbody);

			// Room name cell (sticky left)
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
				const key     = `${room.name}|${d}`;
				const chips   = lookup[key] || [];

				const $td = $(`<td class="mr-td-day${today ? ' is-today' : ''}${weekend ? ' is-weekend' : ''}">`)
					.appendTo($tr)
					.on('click', e => {
						if ($(e.target).closest('.mr-chip').length) return;
						frappe.new_doc('Room Reservation', {
							meeting_room: room.name,
							start_time: date.format('YYYY-MM-DD') + ' 09:00:00',
						});
					});

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
			}
		}
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
