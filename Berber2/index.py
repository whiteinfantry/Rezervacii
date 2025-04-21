from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import MySQLdb
from datetime import datetime, timedelta

app = Flask(__name__)

app.secret_key = "your_secret_key"  # KO PROVERUVAS SESIJATA

USERNAME = "SampleUsername"
PASSWORD = "SamplePassword"



def get_awaiting_slots():
    db = MySQLdb.connect(host="localhost", user="root", passwd="Berberis!a", db="berber")
    cursor = db.cursor()

    query = """
    SELECT * 
    FROM berber.berbertabela 
    WHERE status = 0
    """
    cursor.execute(query)
    data = cursor.fetchall()
    db.close()
    formatted_data = []
    for row in data:
        slot_id, den, mesec, godina, pocetok, kontakt, info, status = row
        
        pocetok_str = f"{pocetok.seconds // 3600:02d}:{(pocetok.seconds % 3600) // 60:02d}"
        
        formatted_data.append({
            'slot_id': slot_id,
            'den': den, 
            'mesec': mesec,
            'pocetok': pocetok_str,
            'kontakt': kontakt, 
            'info': info,
        })

    return formatted_data



def get_db():
    # Get today's date and the next 6 days
    today = datetime.today()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    # Prepare SQL conditions for the next 7 days
    date_conditions = " OR ".join([
        f"(godina = {d.split('-')[0]} AND mesec = {int(d.split('-')[1])} AND den = {int(d.split('-')[2])})"
        for d in dates
    ])

    db = MySQLdb.connect(host="localhost", user="root", passwd="Berberis!a", db="berber")
    cursor = db.cursor()
    
    # sekoi 7 dena
    query = f"""
    SELECT * 
    FROM berber.berbertabela 
    WHERE {date_conditions}
    """
    cursor.execute(query)
    data = cursor.fetchall()
    db.close()

    
    formatted_data = []
    for row in data:
        slot_id, den, mesec, godina, pocetok, kontakt, info, status = row
        
        
        pocetok_str = f"{pocetok.seconds // 3600:02d}:{(pocetok.seconds % 3600) // 60:02d}"
        
        formatted_data.append({
            'slot_id': slot_id, 
            'den': den, 
            'mesec': mesec, 
            'godina': godina,
            'pocetok': pocetok_str,
            'kontakt': kontakt, 
            'info': info,
            'status': status
        })

    return formatted_data

@app.route('/getAvailableSlots', methods=['GET'])
def get_available_slots():
    try:
        month = int(request.args.get('month'))
        day = int(request.args.get('day'))
        year = int(request.args.get('year')) 

        conn = MySQLdb.connect(host="localhost", user="root", passwd="Berberis!a", db="berber")
        cursor = conn.cursor()

        query = """
        SELECT pocetok
        FROM berbertabela
        WHERE mesec = %s AND den = %s AND godina = %s
        """
        cursor.execute(query, (month, day, year))
        slots = cursor.fetchall()

        cursor.close()
        conn.close()

        if slots:#pocetok_str = f"{pocetok.seconds // 3600:02d}:{(pocetok.seconds % 3600) // 60:02d}"
            available_slots = [
            f"{(slot[0].seconds // 3600):02d}:{(slot[0].seconds % 3600) // 60:02d}" 
            for slot in slots
            ]            
            return jsonify(available_slots)
        else:
            return jsonify([])

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch data"}), 500  # Return error if any exception occurs



@app.route('/submit_proposal', methods=['POST'])
def submit_proposal():
    print("AAAAAAAAAAAAAAAAA")
    name = request.form.get('name')
    phone = request.form.get('phone')
    time_slot = request.form.get('time_slot') 
    day = request.form.get('day')
    month = request.form.get('month')
    year = request.form.get('year')  # hardkodirano 2025
    print(f"{name}, {phone}, {time_slot}, {day}, {month}, {year}")
    if not name or not phone or not time_slot or not day or not month or not year:
        #TUKA NEUSPESNO
        flash("Неуспешно!", "danger")
        return render_template('index.html', sent="failure")

    day = int(day)
    month = int(month)
    year = int(year) 

    db = MySQLdb.connect(host="localhost", user="root", passwd="Berberis!a", db="berber")
    cursor = db.cursor()

    query = """
    INSERT INTO berber.berbertabela (den, mesec, godina, pocetok, kontakt, info, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE kontakt = VALUES(kontakt), info = VALUES(info), status = VALUES(status)
    """
    cursor.execute(query, (day, month, year, time_slot, phone, name, 0))
    db.commit()
    db.close()
    #TUKA USPESNO
    flash(f"Закажано! Се гледаме на {day}.{month}.{year} во {time_slot} часот!", "success")
    return redirect(url_for('home'))

@app.route('/get_proposals', methods=['GET'])
def get_awaiting():
    occupied_slots = get_awaiting_slots()  # Get data where status == 1
    return jsonify(occupied_slots)



@app.route('/update_proposal', methods=['POST'])
def update_proposal():
    data = request.json
    print(f"Received data: {data}")  
    
    slot_id = data.get('slot_id')
    new_status = data.get('status')

    if slot_id is None or new_status is None:
        return jsonify({"success": False, "error": "Missing slot_id or status"}), 400
    
    print(f"slot_id: {slot_id}, new_status: {new_status}") 
    
    try:
        slot_id = int(slot_id)  
        new_status = int(new_status)  
    except ValueError:
        return jsonify({"success": False, "error": "Invalid data type for slot_id or status"}), 400

    # Ensure the new status is valid (1 = approved, 3 = rejected)
    if new_status not in [1, 3]:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    try:
        db = MySQLdb.connect(host="localhost", user="root", passwd="Berberis!a", db="berber")
        cursor = db.cursor()
        
        # Execute the query to update the status
        cursor.execute("UPDATE berber.berbertabela SET status = %s WHERE slot_id = %s", (new_status, slot_id))
        db.commit()
        db.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/logirajse', methods=['GET', 'POST'])
def logirajSe():
    if request.method == 'POST':
        input_username = request.form['username']
        input_password = request.form['password']
        
        if input_username ==USERNAME and input_password == PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('home'))
        else:
            return "Invalid credentials, try again", 401

    return render_template('login.html') 


@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('berberlogin'))

    return "Welcome, Admin! Here are the pending reservations."

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('berberlogin'))

@app.route('/is_admin')
def is_admin():
    return {"is_admin": session.get('admin_logged_in', False)}


@app.route('/')
def home():
    data = get_db()
   # data = get_all_records()
    return render_template('index.html', data=data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
