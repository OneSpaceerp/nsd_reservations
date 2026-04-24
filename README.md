# NSD Reservations
Meeting Room Reservation Module for ERPNext v16

## Installation
1. Create a new site or use existing ERPNext v16 site
2. Get the app: `bench get-app <repo-url>`
3. Install the app: `bench install-app nsd_reservations`
4. Run migrations: `bench migrate`
5. Assign roles:
   - `Meeting Room User`: For employees creating reservations
   - `Meeting Room Manager`: For managers approving reservations

## Usage
- Create Meeting Rooms via Meeting Room DocType
- Employees create reservations via Room Reservation form or Calendar view
- Managers approve/reject pending reservations via Workflow
- Calendar view shows all reservations with color-coded status

## Features
- Meeting Room master data
- Room Reservation with approval workflow
- Overlap conflict prevention
- Calendar view with business hours
- Role-based permissions

## Testing
Run tests: `bench run-tests --app nsd_reservations`
