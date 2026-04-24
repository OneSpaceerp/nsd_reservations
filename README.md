# NSD Reservations

Meeting Room Reservation Module for ERPNext v16

## Overview

NSD Reservations is a custom Frappe/ERPNext application that provides a complete meeting room booking workflow with calendar-based scheduling, approval controls, conflict prevention, and room master data management.

## Features

- **Meeting Room Management** - Master data for physical meeting rooms with capacity tracking
- **Room Reservation System** - Create and manage room bookings with full validation
- **Calendar View** - Visual calendar showing reservations by room and time
- **Approval Workflow** - Manager approval required before reservations become active
- **Conflict Prevention** - Automatic blocking of overlapping approved reservations
- **Email Notifications** - Alerts for submission, approval, and rejection events
- **Reports & Dashboard** - Reservation summary and operational visibility
- **Role-based Access** - Meeting Room User and Meeting Room Manager roles

## Requirements

- ERPNext v16 or Frappe Framework v16
- Python 3.10+
- MariaDB 10.5+

## Installation

### Method 1: Production Installation

1. Navigate to your Frappe/ERPNext bench:
   ```bash
   cd /path/to/your/bench
   ```

2. Clone the app repository into your apps directory:
   ```bash
   git clone https://github.com/your-repo/nsd_reservations.git apps/nsd_reservations
   ```

3. Install the app:
   ```bash
   bench get-app nsd_reservations
   ```

4. Install on specific site:
   ```bash
   bench --site yoursite.com install-app nsd_reservations
   ```

5. Migrate the site:
   ```bash
   bench --site yoursite.com migrate
   ```

### Method 2: Development Installation

1. Clone into apps directory:
   ```bash
   cd /path/to/bench
   git clone https://github.com/your-repo/nsd_reservations.git apps/nsd_reservations
   ```

2. Install dependencies:
   ```bash
   cd apps/nsd_reservations
   pip install -r requirements.txt
   ```

3. Add to bench's Procfile for development if needed
4. Restart bench services

## App Structure

```
nsd_reservations/
├── nsd_reservations/
│   ├── __init__.py
│   ├── hooks.py
│   ├── modules.txt
│   ├── setup.py
│   ├── requirements.txt
│   ├── meeting_management/
│   │   ├── __init__.py
│   │   ├── doctype/
│   │   │   ├── meeting_room/
│   │   │   │   ├── meeting_room.json
│   │   │   │   ├── meeting_room.py
│   │   │   │   ├── meeting_room.js
│   │   │   │   └── test_meeting_room.py
│   │   │   └── room_reservation/
│   │   │       ├── room_reservation.json
│   │   │       ├── room_reservation.py
│   │   │       ├── room_reservation.js
│   │   │       └── test_room_reservation.py
│   │   ├── report/
│   │   │   └── room_reservation_summary/
│   │   │       ├── room_reservation_summary.json
│   │   │       └── room_reservation_summary.py
│   │   ├── workspace/
│   │   │   └── meeting_management/
│   │   │       └── meeting_management.json
│   │   └── custom/
│   │       ├── reservation_submit_for_approval.json
│   │       ├── reservation_approved.json
│   │       └── reservation_rejected.json
│   ├── config/
│   │   ├── __init__.py
│   │   ├── desktop.py
│   │   └── docs.py
│   └── public/
│       ├── css/
│       └── js/
├── README.md
├── requirements.txt
└── setup.py
```

## Configuration

### Creating Roles

After installation, the following roles will be created automatically via fixtures:

- **Meeting Room User** - Can create and view reservations
- **Meeting Room Manager** - Can approve/reject reservations, manage rooms

### Creating Meeting Rooms

1. Go to Meeting Management workspace
2. Click on "Meeting Rooms" link
3. Create new rooms with name, capacity, and location

Default rooms:
- Main Meeting Room (capacity: 20)
- Casual Meeting Room (capacity: 6)

### Workflow States

The approval workflow has the following states:
1. **Draft** - Initial state when created
2. **Pending Manager Approval** - Submitted for review
3. **Reserved** - Approved and active
4. **Rejected** - Not approved
5. **Cancelled** - Cancelled after approval

## Usage

### Creating a Reservation

1. Navigate to Meeting Management workspace
2. Click "New Reservation"
3. Fill in the form:
   - Select meeting room
   - Set start and end time
   - Person in charge (defaults to current user)
   - Department
   - Meeting reason
   - Number of attendees
4. Click "Submit for Approval"

### Approving a Reservation (Manager)

1. View pending reservations in the list
2. Open the pending reservation
3. Click "Approve" or "Reject"
4. If rejecting, provide a reason

### Calendar View

1. Go to Room Reservation list
2. Click "Calendar" toggle button
3. Filter by room, department, or status

## Validation Rules

- Start time must be before end time
- Reservation duration max 4 hours
- Room must be active
- Attendees cannot exceed room capacity
- No overlap with approved reservations

## Development

### Running Tests

```bash
bench --site test-site run-tests --app nsd_reservations
```

### Enabling Developer Mode

In your `sites/site1.local/site_config.json`:
```json
{
  "developer_mode": 1
}
```

### Rebuilding App

After making changes to JSON files:
```bash
bench --site yoursite.com migrate
```

Or for development:
```bash
bench console
# In console:
import nsd_reservations
nsd_reservations.setup.install()
```

## Troubleshooting

### App Not Appearing

1. Check if installed: `bench --site yoursite.com list-apps`
2. Try migrating: `bench --site yoursite.com migrate`
3. Check bench error logs

### Workflow Not Working

1. Go to Workflow list
2. Check "Meeting Reservation Approval" is active
3. Verify fixtures are loaded

### Permissions Issues

1. Check Role Permission Manager
2. Verify user has correct role assigned
3. Clear cache: `bench --site yoursite.com clear-website-cache`

## License

MIT License

## Support

For issues and feature requests, please create an issue in the repository.