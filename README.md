<<<<<<< HEAD
# RFMS-Fleetx-2.1
Radiance is a web-based Employee Bus Route Tracking system that lets company authorities manage driver routes and lets drivers log daily trip data in real time. Admins create routes, assign drivers, and view live analytics (on-time %, headcount, utilization) and a monthly calendar of trip history. 
=======
# Radiance App

A web-based fleet and route monitoring system for managing driver login, trip creation, route tracking, trip analysis, and reporting. The project includes a Flask backend and a set of HTML pages for the admin and driver workflows.

## Overview

This application allows:

- Admin login and authority access
- Driver login and trip management
- Route creation with scheduled start times and stop lists
- Trip start/end workflow for drivers
- Passenger/headcount tracking per stop
- Analysis and reporting dashboards
- Calendar-style trip summaries by day and driver

## Project Structure

```text
radiance__app/
├── 00_opening.html
├── 01_admin_login.html
├── 01_driver_login.html
├── 02_driver_dashboard.html
├── 03_confirm_trip.html
├── 03_route.html
├── 04_end_trip.html
├── 04_new_trip.html
├── 05_calendar.html
├── 05_driver_profile.html
├── 06_analysis.html
├── 07_report.html
├── 08_admin_profile.html
├── 09_add_driver.html
├── 10_dashboard_analysis.html
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── seed.py
│   └── requirements.txt
└── README.md
```

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, Flask
- Database: MySQL / MariaDB via `mysql-connector-python`
- CORS support: `flask-cors`

## Prerequisites

Before running the application, make sure you have:

- Python 3.9+
- MySQL or MariaDB running locally
- XAMPP or another MySQL server instance if you are using the default setup

## Database Setup

The backend connects to MySQL using the following default configuration in `backend/db.py`:

```python
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="radiance_bus_tracking"
)
```

Create a database named:

```sql
radiance_bus_tracking
```

Then create the required tables for drivers, admins, routes, trips, stops, and headcounts used by the app.

## Setup

1. Open a terminal in the `backend` folder.
2. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
```

3. Activate the environment:

- Windows:

```bash
venv\Scripts\activate
```

- macOS/Linux:

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Backend

From the `backend` folder:

```bash
python app.py
```

The API will run on:

```text
http://127.0.0.1:5000
```

## Seed Test Accounts

A test admin and driver account can be created by running:

```bash
python seed.py
```

Default credentials created by the script:

- Admin email: `admin@company.com`
- Admin password: `admin123`
- Driver ID: `DRV1023`
- Driver password: `driver123`

## Open the App

Open the `.html` pages in the project root in a browser, such as:

- `00_opening.html` for the landing page
- `01_admin_login.html` for admin login
- `01_driver_login.html` for driver login

## Main API Endpoints

The backend exposes endpoints such as:

- `POST /api/admin/login`
- `POST /api/driver/login`
- `POST /api/routes`
- `GET /api/routes`
- `DELETE /api/routes/<route_id>`
- `POST /api/drivers`
- `GET /api/drivers`
- `GET /api/driver/<driver_id>/route`
- `POST /api/trips/start`
- `POST /api/trips/end`
- `POST /api/trips/<trip_id>/headcount`
- `GET /api/analysis`
- `GET /api/report`
- `GET /api/calendar`

## Notes

- The project is designed for local development and demo use.
- The frontend calls the backend directly using `http://127.0.0.1:5000`.
- If you change the database credentials or database name, update the values in `backend/db.py`.

## License

This project is provided as-is for educational or local development use.
>>>>>>> 02391b5 (first commit)
