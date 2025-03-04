import MySQLdb

try:
    db = MySQLdb.connect(host="localhost", user="root", passwd="Berberis!a", db="berber")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM berber.berbertabela")  # Adjust table name if necessary
    data = cursor.fetchall()
    print(data)  # Check if this works and prints data from the database
except MySQLdb.Error as e:
    print(f"Error: {e}")