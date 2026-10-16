import mysql.connector

def get_db_connection():
    """
    Opens a fresh connection to the MySQL/MariaDB database
    running in XAMPP.

    Default XAMPP MySQL has:
      host = localhost
      user = root
      password = "" (empty, unless you set one)
    """
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",              # change this if you set a root password in XAMPP
        database="radiance_bus_tracking"
    )
    return connection