"""
Run this file ONCE to create a test admin and a test driver account.
Usage:  python seed.py
"""

from werkzeug.security import generate_password_hash
from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# ---------- Test Admin ----------
admin_email = "admin@company.com"
admin_password = "admin123"          # you'll log in with this
admin_hash = generate_password_hash(admin_password)

cursor.execute(
    """INSERT INTO admins (name, email, password_hash, role, phone)
       VALUES (%s, %s, %s, %s, %s)""",
    ("Admin User", admin_email, admin_hash, "admin", "+91 98765 43210")
)

# ---------- Test Driver ----------
driver_code = "DRV1023"
driver_password = "driver123"        # you'll log in with this
driver_hash = generate_password_hash(driver_password)

cursor.execute(
    """INSERT INTO drivers (driver_code, name, password_hash, phone, vehicle_number)
       VALUES (%s, %s, %s, %s, %s)""",
    (driver_code, "Ramesh Kumar", driver_hash, "+91 98765 43210", "TN 09 AB 1234")
)

conn.commit()
cursor.close()
conn.close()

print("Test accounts created successfully!")
print(f"Admin login  -> email: {admin_email} | password: {admin_password}")
print(f"Driver login -> Driver ID: {driver_code} | password: {driver_password}")