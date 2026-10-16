from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection

app = Flask(__name__)
CORS(app)


# ==========================================================
# ADMIN / AUTHORITY LOGIN
# ==========================================================

@app.route("/api/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password required."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM admins WHERE email = %s",
        (email,)
    )

    admin = cursor.fetchone()

    cursor.close()
    conn.close()

    if not admin:
        return jsonify({
            "success": False,
            "message": "No account found with that email."
        }), 404

    if not check_password_hash(
        admin["password_hash"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Incorrect password."
        }), 401

    admin.pop("password_hash")

    return jsonify({
        "success": True,
        "admin": admin
    })


# ==========================================================
# DRIVER LOGIN
# ==========================================================

@app.route("/api/driver/login", methods=["POST"])
def driver_login():

    data = request.get_json()

    driver_code = data.get("driver_code")
    password = data.get("password")

    if not driver_code or not password:
        return jsonify({
            "success": False,
            "message": "Driver ID and password required."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM drivers WHERE driver_code = %s",
        (driver_code,)
    )

    driver = cursor.fetchone()

    cursor.close()
    conn.close()

    if not driver:
        return jsonify({
            "success": False,
            "message": "No driver found with that ID."
        }), 404

    if not check_password_hash(
        driver["password_hash"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Incorrect password."
        }), 401

    driver.pop("password_hash")

    return jsonify({
        "success": True,
        "driver": driver
    })


# ==========================================================
# CREATE ROUTE
# ==========================================================

@app.route("/api/routes", methods=["POST"])
def create_route():

    data = request.get_json()

    driver_name = data.get("driver_name")
    actual_seating_number = data.get("actual_seating_number")
    vehicle_number = data.get("vehicle_number")
    start_point = data.get("start_point")
    end_point = data.get("end_point")
    scheduled_start_time = data.get(
        "scheduled_start_time"
    ) or "09:00:00"

    stops = data.get("stops", [])

    if (
        not driver_name
        or not actual_seating_number
        or not start_point
        or not end_point
    ):
        return jsonify({
            "success": False,
            "message": (
                "Driver name, seating number, "
                "start point, and end point "
                "are all required."
            )
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM drivers
        WHERE LOWER(name) = LOWER(%s)
        """,
        (driver_name,)
    )

    driver = cursor.fetchone()

    if not driver:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": (
                f"No driver named '{driver_name}' found. "
                "Ask an admin to add this driver first."
            )
        }), 404

    if vehicle_number:

        cursor.execute(
            """
            UPDATE drivers
            SET vehicle_number = %s
            WHERE driver_id = %s
            """,
            (
                vehicle_number,
                driver["driver_id"]
            )
        )

    route_name = (
        f"{start_point} to {end_point}"
    )

    cursor.execute(
        """
        INSERT INTO routes
        (
            driver_id,
            route_name,
            start_point,
            end_point,
            actual_seating_number,
            scheduled_start_time
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            driver["driver_id"],
            route_name,
            start_point,
            end_point,
            actual_seating_number,
            scheduled_start_time
        )
    )

    route_id = cursor.lastrowid

    for index, stop_name in enumerate(stops):

        if stop_name.strip() == "":
            continue

        cursor.execute(
            """
            INSERT INTO stops
            (
                route_id,
                stop_name,
                stop_order
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                route_id,
                stop_name.strip(),
                index + 1
            )
        )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "route_id": route_id
    })


# ==========================================================
# GET ALL ROUTES
# ==========================================================

@app.route("/api/routes", methods=["GET"])
def get_all_routes():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            r.route_id,
            r.route_name,
            r.start_point,
            r.end_point,
            r.actual_seating_number,
            r.scheduled_start_time,
            r.created_at,
            d.driver_id,
            d.name AS driver_name,
            d.phone,
            d.vehicle_number

        FROM routes r

        JOIN drivers d
            ON r.driver_id = d.driver_id

        ORDER BY r.created_at DESC
        """
    )

    routes = cursor.fetchall()

    for route in routes:

        if route.get("scheduled_start_time") is not None:
            route["scheduled_start_time"] = str(
                route["scheduled_start_time"]
            )

        if route.get("created_at") is not None:
            route["created_at"] = str(
                route["created_at"]
            )

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "routes": routes
    })


# ==========================================================
# DELETE ROUTE
# ==========================================================

@app.route(
    "/api/routes/<int:route_id>",
    methods=["DELETE"]
)
def delete_route(route_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT route_id
            FROM routes
            WHERE route_id = %s
            """,
            (route_id,)
        )

        route = cursor.fetchone()

        if not route:

            cursor.close()
            conn.close()

            return jsonify({
                "success": False,
                "message": "Route not found."
            }), 404

        cursor.execute(
            """
            DELETE FROM stop_headcounts
            WHERE trip_id IN
            (
                SELECT trip_id
                FROM trips
                WHERE route_id = %s
            )
            """,
            (route_id,)
        )

        cursor.execute(
            """
            DELETE FROM trips
            WHERE route_id = %s
            """,
            (route_id,)
        )

        cursor.execute(
            """
            DELETE FROM stops
            WHERE route_id = %s
            """,
            (route_id,)
        )

        cursor.execute(
            """
            DELETE FROM routes
            WHERE route_id = %s
            """,
            (route_id,)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Route deleted successfully."
        })

    except Exception as e:

        conn.rollback()

        cursor.close()
        conn.close()

        print(
            "DELETE ROUTE ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": (
                "Could not delete route: "
                + str(e)
            )
        }), 500


# ==========================================================
# CREATE DRIVER
# ==========================================================

@app.route("/api/drivers", methods=["POST"])
def create_driver():

    data = request.get_json()

    driver_code = data.get("driver_code")
    name = data.get("name")
    password = data.get("password")
    phone = data.get("phone")
    vehicle_number = data.get("vehicle_number")

    if not driver_code or not name or not password:

        return jsonify({
            "success": False,
            "message": (
                "Driver ID, name, and password "
                "are required."
            )
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT driver_id
        FROM drivers
        WHERE driver_code = %s
        """,
        (driver_code,)
    )

    existing = cursor.fetchone()

    if existing:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": (
                f"Driver ID '{driver_code}' "
                "already exists."
            )
        }), 409

    password_hash = generate_password_hash(
        password
    )

    cursor.execute(
        """
        INSERT INTO drivers
        (
            driver_code,
            name,
            password_hash,
            phone,
            vehicle_number
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            driver_code,
            name,
            password_hash,
            phone,
            vehicle_number
        )
    )

    driver_id = cursor.lastrowid

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "driver_id": driver_id
    })


# ==========================================================
# GET ALL DRIVERS
# ==========================================================

@app.route("/api/drivers", methods=["GET"])
def get_all_drivers():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            driver_id,
            driver_code,
            name,
            phone,
            vehicle_number

        FROM drivers
        """
    )

    drivers = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "drivers": drivers
    })


# ==========================================================
# GET DRIVER ROUTE + STOPS
# ==========================================================

@app.route(
    "/api/driver/<int:driver_id>/route",
    methods=["GET"]
)
def get_driver_route(driver_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            route_id,
            route_name,
            start_point,
            end_point,
            actual_seating_number,
            scheduled_start_time

        FROM routes

        WHERE driver_id = %s

        ORDER BY created_at DESC

        LIMIT 1
        """,
        (driver_id,)
    )

    route = cursor.fetchone()

    if not route:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "No route assigned yet."
        }), 404

    route["scheduled_start_time"] = str(
        route["scheduled_start_time"]
    )

    cursor.execute(
        """
        SELECT
            stop_id,
            stop_name,
            stop_order,
            expected_arrival

        FROM stops

        WHERE route_id = %s

        ORDER BY stop_order ASC
        """,
        (route["route_id"],)
    )

    stops = cursor.fetchall()

    for stop in stops:

        if stop.get("expected_arrival") is not None:
            stop["expected_arrival"] = str(
                stop["expected_arrival"]
            )

    cursor.execute(
        """
        SELECT
            trip_id,
            trip_status,
            start_time,
            end_time

        FROM trips

        WHERE route_id = %s
          AND trip_date = CURDATE()

        ORDER BY trip_id DESC

        LIMIT 1
        """,
        (route["route_id"],)
    )

    todays_trip = cursor.fetchone()

    todays_headcounts = {}

    if todays_trip:

        if todays_trip.get("start_time") is not None:
            todays_trip["start_time"] = str(
                todays_trip["start_time"]
            )

        if todays_trip.get("end_time") is not None:
            todays_trip["end_time"] = str(
                todays_trip["end_time"]
            )

        cursor.execute(
            """
            SELECT
                stop_id,
                headcount

            FROM stop_headcounts

            WHERE trip_id = %s
            """,
            (todays_trip["trip_id"],)
        )

        for row in cursor.fetchall():

            todays_headcounts[
                row["stop_id"]
            ] = row["headcount"]

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "route": route,
        "stops": stops,
        "todays_trip": todays_trip,
        "todays_headcounts": todays_headcounts
    })


# ==========================================================
# START TRIP
# ==========================================================

@app.route(
    "/api/trips/start",
    methods=["POST"]
)
def start_trip():

    data = request.get_json()

    route_id = data.get("route_id")
    driver_id = data.get("driver_id")

    if not route_id or not driver_id:

        return jsonify({
            "success": False,
            "message": (
                "route_id and driver_id required."
            )
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT scheduled_start_time
        FROM routes
        WHERE route_id = %s
        """,
        (route_id,)
    )

    route = cursor.fetchone()

    scheduled_time = (
        route["scheduled_start_time"]
        if route
        else None
    )

    cursor.execute(
        """
        INSERT INTO trips
        (
            route_id,
            driver_id,
            trip_date,
            start_time,
            trip_status,
            timing_status
        )

        VALUES
        (
            %s,
            %s,
            CURDATE(),
            NOW(),
            'running',

            CASE
                WHEN CURTIME() > %s
                THEN 'late'
                ELSE 'on_time'
            END
        )
        """,
        (
            route_id,
            driver_id,
            scheduled_time
        )
    )

    trip_id = cursor.lastrowid

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "trip_id": trip_id
    })


# ==========================================================
# END TRIP
# ==========================================================

@app.route(
    "/api/trips/end",
    methods=["POST"]
)
def end_trip():

    data = request.get_json()

    trip_id = data.get("trip_id")

    if not trip_id:

        return jsonify({
            "success": False,
            "message": "trip_id required."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE trips

        SET
            end_time = NOW(),
            trip_status = 'completed'

        WHERE trip_id = %s
        """,
        (trip_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True
    })


# ==========================================================
# SAVE HEADCOUNT
# ==========================================================

@app.route(
    "/api/trips/<int:trip_id>/headcount",
    methods=["POST"]
)
def save_headcount(trip_id):

    data = request.get_json()

    stop_id = data.get("stop_id")
    headcount = data.get("headcount")

    if stop_id is None or headcount is None:

        return jsonify({
            "success": False,
            "message": (
                "stop_id and headcount required."
            )
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id
        FROM stop_headcounts

        WHERE trip_id = %s
          AND stop_id = %s
        """,
        (
            trip_id,
            stop_id
        )
    )

    existing = cursor.fetchone()

    if existing:

        cursor.execute(
            """
            UPDATE stop_headcounts
            SET headcount = %s
            WHERE id = %s
            """,
            (
                headcount,
                existing["id"]
            )
        )

    else:

        cursor.execute(
            """
            INSERT INTO stop_headcounts
            (
                trip_id,
                stop_id,
                headcount
            )

            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                trip_id,
                stop_id,
                headcount
            )
        )

    cursor.execute(
        """
        SELECT
            SUM(headcount) AS total

        FROM stop_headcounts

        WHERE trip_id = %s
        """,
        (trip_id,)
    )

    total = (
        cursor.fetchone()["total"]
        or 0
    )

    cursor.execute(
        """
        UPDATE trips
        SET total_headcount = %s
        WHERE trip_id = %s
        """,
        (
            total,
            trip_id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "total_headcount": total
    })


# ==========================================================
# ANALYSIS
# ==========================================================

@app.route(
    "/api/analysis",
    methods=["GET"]
)
def get_analysis():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_trips,

            SUM(
                CASE
                    WHEN timing_status = 'on_time'
                    THEN 1
                    ELSE 0
                END
            ) AS on_time_trips,

            SUM(
                CASE
                    WHEN timing_status = 'late'
                    THEN 1
                    ELSE 0
                END
            ) AS late_trips,

            COALESCE(
                SUM(total_headcount),
                0
            ) AS total_headcount

        FROM trips

        WHERE trip_status = 'completed'
        """
    )

    stats = cursor.fetchone()

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(actual_seating_number),
                0
            ) AS total_seats

        FROM routes
        """
    )

    seats = cursor.fetchone()

    cursor.close()
    conn.close()

    total_trips = (
        stats["total_trips"]
        or 0
    )

    total_headcount = (
        stats["total_headcount"]
        or 0
    )

    total_seats = (
        seats["total_seats"]
        or 0
    )

    avg_headcount = (
        round(
            total_headcount / total_trips,
            1
        )
        if total_trips > 0
        else 0
    )

    utilization = (
        round(
            (
                total_headcount /
                total_seats
            ) * 100,
            1
        )
        if total_seats > 0
        else 0
    )

    return jsonify({
        "success": True,
        "on_time_trips":
            stats["on_time_trips"] or 0,
        "late_trips":
            stats["late_trips"] or 0,
        "total_trips":
            total_trips,
        "total_headcount":
            total_headcount,
        "avg_headcount":
            avg_headcount,
        "utilization":
            utilization
    })


# ==========================================================
# REPORT
# ==========================================================

@app.route(
    "/api/report",
    methods=["GET"]
)
def get_report():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            t.trip_date,
            d.name AS driver_name,
            d.phone,
            t.start_time,
            t.end_time,
            t.timing_status,
            t.total_headcount

        FROM trips t

        JOIN drivers d
            ON t.driver_id = d.driver_id

        ORDER BY
            t.trip_date DESC,
            t.trip_id DESC

        LIMIT 100
        """
    )

    trips = cursor.fetchall()

    for trip in trips:

        trip["trip_date"] = (
            str(trip["trip_date"])
            if trip.get("trip_date")
            else ""
        )

        trip["start_time"] = (
            str(trip["start_time"])
            if trip.get("start_time")
            else ""
        )

        trip["end_time"] = (
            str(trip["end_time"])
            if trip.get("end_time")
            else ""
        )

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "trips": trips
    })


# ==========================================================
# TRIP TABLE (full per-trip columns for the Dashboard Analysis page)
# ==========================================================

@app.route(
    "/api/trip-table",
    methods=["GET"]
)
def get_trip_table():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            r.route_name,
            r.start_point,
            r.end_point,
            r.actual_seating_number,
            t.total_headcount,
            t.start_time,
            t.end_time,
            t.trip_status,
            t.timing_status

        FROM trips t

        JOIN routes r
            ON t.route_id = r.route_id

        ORDER BY
            t.trip_date DESC,
            t.trip_id DESC

        LIMIT 100
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    trips = []

    for row in rows:

        seats = row["actual_seating_number"] or 0
        headcount = row["total_headcount"] or 0

        utilization = (
            round((headcount / seats) * 100, 1)
            if seats
            else 0
        )

        start_time = row["start_time"]
        end_time = row["end_time"]

        travel_time = ""

        if start_time and end_time:

            delta = end_time - start_time if hasattr(end_time, "__sub__") else None

            try:
                total_seconds = int(delta.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                travel_time = f"{hours}h {minutes}m" if hours else f"{minutes}m"
            except Exception:
                travel_time = ""

        trips.append({
            "route_name": row["route_name"],
            "start_point": row["start_point"],
            "end_point": row["end_point"],
            "actual_seating_number": seats,
            "total_headcount": headcount,
            "utilization": utilization,
            "start_time": str(start_time) if start_time else "",
            "end_time": str(end_time) if end_time else "",
            "travel_time": travel_time,
            "trip_status": row["trip_status"],
            "timing_status": row["timing_status"]
        })

    return jsonify({
        "success": True,
        "trips": trips
    })


# ==========================================================
# CALENDAR
# ==========================================================

@app.route(
    "/api/calendar",
    methods=["GET"]
)
def get_calendar_data():

    year = request.args.get("year")
    month = request.args.get("month")
    driver_id = request.args.get("driver_id")


    if not year or not month:

        return jsonify({
            "success": False,
            "message": (
                "year and month are required."
            )
        }), 400


    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


    # ======================================================
    # GET DRIVER / ROUTE INFORMATION
    # ======================================================

    driver_name = ""
    route_name = ""


    if driver_id:

        cursor.execute(
            """
            SELECT
                d.name AS driver_name,
                r.route_name

            FROM drivers d

            LEFT JOIN routes r
                ON d.driver_id = r.driver_id

            WHERE d.driver_id = %s

            ORDER BY r.created_at DESC

            LIMIT 1
            """,
            (driver_id,)
        )

        driver_info = cursor.fetchone()


        if driver_info:

            driver_name = (
                driver_info["driver_name"]
                or ""
            )

            route_name = (
                driver_info["route_name"]
                or ""
            )


    # ======================================================
    # SAME CALENDAR FORMULA
    # ONLY ADD DRIVER FILTER
    # ======================================================

    if driver_id:

        cursor.execute(
            """
            SELECT
                DAY(t.trip_date) AS day,

                COALESCE(
                    SUM(t.total_headcount),
                    0
                ) AS total_headcount,

                COALESCE(
                    SUM(r.actual_seating_number),
                    0
                ) AS total_seats,

                SUM(
                    CASE
                        WHEN t.timing_status = 'late'
                        THEN 1
                        ELSE 0
                    END
                ) AS late_count

            FROM trips t

            JOIN routes r
                ON t.route_id = r.route_id

            WHERE YEAR(t.trip_date) = %s

              AND MONTH(t.trip_date) = %s

              AND t.trip_status = 'completed'

              AND t.driver_id = %s

            GROUP BY DAY(t.trip_date)
            """,
            (
                year,
                month,
                driver_id
            )
        )

    else:

        # Keeps old behaviour if no driver is selected

        cursor.execute(
            """
            SELECT
                DAY(t.trip_date) AS day,

                COALESCE(
                    SUM(t.total_headcount),
                    0
                ) AS total_headcount,

                COALESCE(
                    SUM(r.actual_seating_number),
                    0
                ) AS total_seats,

                SUM(
                    CASE
                        WHEN t.timing_status = 'late'
                        THEN 1
                        ELSE 0
                    END
                ) AS late_count

            FROM trips t

            JOIN routes r
                ON t.route_id = r.route_id

            WHERE YEAR(t.trip_date) = %s

              AND MONTH(t.trip_date) = %s

              AND t.trip_status = 'completed'

            GROUP BY DAY(t.trip_date)
            """,
            (
                year,
                month
            )
        )


    rows = cursor.fetchall()


    # ======================================================
    # SAME PERCENTAGE FORMULA
    # ======================================================

    calendar_data = {}


    for row in rows:

        total_headcount = (
            row["total_headcount"]
        )

        total_seats = (
            row["total_seats"]
        )


        percentage = (
            round(
                (
                    total_headcount /
                    total_seats
                ) * 100
            )
            if total_seats > 0
            else 0
        )


        calendar_data[
            str(row["day"])
        ] = {

            "status":
                "Late"
                if row["late_count"] > 0
                else "On Time",

            "headcount":
                f"{total_headcount}/{total_seats}",

            "percentage":
                f"{percentage}%"
        }


    cursor.close()
    conn.close()


    return jsonify({

        "success": True,

        "calendar_data":
            calendar_data,

        "driver_name":
            driver_name,

        "route_name":
            route_name

    })


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route(
    "/",
    methods=["GET"]
)
def health_check():

    return jsonify({
        "status":
            "Radiance backend is running."
    })


# ==========================================================
# RUN SERVER
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )