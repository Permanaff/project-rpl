from flask import Flask, render_template, session, request , redirect, url_for, flash, jsonify, send_file, abort
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_cors import CORS
from dotenv import load_dotenv
from urllib.parse import quote_plus
from midtransclient import Snap, CoreApi
import requests
import os
import random
import string
import qrcode
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CORS(app, origins=['http://127.0.0.1:4000', 'https://a4a2-202-51-208-50.ngrok-free.app'])

core = CoreApi(
    is_production=False,
    server_key= 'SB-Mid-server-MkWPtSUBmoSSOJ4UkdcyilCC',
    client_key='SB-Mid-client-DG3O1SszFRlzErbv'
)

app.config['MYSQL_HOST'] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"]= ''
app.config["MYSQL_DB"] = 'cinema'
app.config["UPLOAD_FOLDER"] = 'static/images/'

mysql = MySQL(app)

@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html')

# @app.route('/booking')
# def booking():
#     return render_template('seat.html')

@app.route('/booking1')
@app.route('/studio1')
def studio1():
    return render_template('studio1.html')



@app.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'inpEmail' in request.form and 'inpPass' in request.form:
        email = request.form['inpEmail']
        passwd = request.form['inpPass']

        cur = mysql.connection.cursor()

        api_url = 'http://127.0.0.1:4000/login'
        api_data = {'email': email, 'password': passwd}
        response = requests.post(api_url, json=api_data)
   
        if response.status_code == 200:
            data = response.json()

            user_id = data[0]['user_id']
            username = data[0]['username']
            level_user = data[0]['level_user']
            nama = data[0]['nama']
            id_theater = data[0]['id_theater']

            if data:
                session['is_logged_in'] = True
                session['user_id'] = user_id
                session['username'] = username
                session['level_user'] = level_user
                session['nama'] = nama
                session['id_theater'] = id_theater

                if session['level_user'] == '1' or session['level_user'] == '2' : 
                    return redirect(url_for('dashboard'))
                
                return redirect(url_for('home'))
        else:
            error_message = "Login Gagal. Email atau password tidak valid."
            flash(error_message, 'error')
            return redirect(url_for('login', error='Login Gagal'))
        cur.close()
    else:
        return render_template('login.html')



@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST" and "inpUser" in request.form and "inpEmail" in request.form and "inpPass" in request.form:
        nama = request.form["firstName"]
        username = request.form["inpUser"]
        no_telp = request.form["inpTelp"]
        alamat = request.form["inpAlamat"]
        email = request.form["inpEmail"]
        passwd = request.form["inpPass"]
        gender = request.form["gender"]
        tanggal_lahir = f"{request.form['year']}-{request.form['month']}-{request.form['day']}"
        level_user = '2'
        # image = 'default-profile.png'
        print(tanggal_lahir)

        data = {
            'nama' : nama,
            'username' : username,
            'no_telp' : no_telp,
            'alamat' : alamat,
            'email' : email,
            'password' : passwd,
            'gender' : gender,
            'tanggal_lahir' : tanggal_lahir,
            'level_user' : level_user
        }

        api_url = 'http://127.0.0.1:4000/register'
        # api_data = {'nama': nama,'username' : username,'no_telp': no_telp, 'alamat': alamat,'password': passwd}
        response = requests.post(api_url, json=data)  

        if response.status_code == 200 : 
            return redirect(url_for('login'))
        else : 
            error_message = "Registrasi Gagal."
            flash(error_message, 'error')
            return redirect(url_for('register', error='Registrasi Gagal'))

    else:
        return render_template('register.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout(): 
    if 'is_logged_in' in session :
        session.pop('is_logged_in', None)
        session.pop('user_id', None)
        session.pop('username', None)
        session.pop('level_user', None)
        session.pop('nama', None)
        session.pop('id_theater', None)
        return redirect(url_for('home'))
    else : 
        return redirect(url_for('login'))
    
@app.route('/login-status', methods=['POST'])
def login_status(): 
    if 'is_logged_in' in session :
        user_id = session['user_id']
        username = session['username']
        level_user = session['level_user'] 
        nama = session['nama'] 
        id_theater = session['id_theater'] 
        return jsonify({'logged_in' : True, 'user_id' : user_id, 'username' : username, 'level_user' : level_user, 'nama' : nama, 'id_theater' : id_theater})
    else : 
        return jsonify({'logged_in' : False})
    



@app.route('/schedule-page/<id_movie>', methods=['GET', 'POST'])
def schedule(id_movie) : 
    if request.method == "POST" : 
        jml_seat = request.form["selectTickets"]
        id_schedule = request.form["inpId"]
        print('jml seat : '+jml_seat)
        print(id_schedule)
        return redirect(url_for('get_schedule_id', id_schedule=id_schedule, jml_seat=jml_seat))
    else : 
        return render_template('schedule-page.html', id_movie = id_movie)


@app.route('/tickets')
def tickets(): 
    return render_template('tickets-info.html')

@app.route('/tes/<int:id>')
def tes(id):
    if id == 1 :
        return render_template('test.html')
    else : 
        return render_template('test2.html')

@app.route('/save-image', methods=['POST'])
def receive_data():
    try:
        file = request.files['file']
        subfolder = request.form.get('subfolder', '') 
        print(file)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
            file.save(file_path)

            return jsonify({'status': 'success', 'message': 'File received and saved successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid file or file extension'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Error receiving and saving file', 'error': str(e)})


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------



@app.route('/add_booking')
def generate_bookingId():
    date = datetime.now().strftime('%y%m%d')
    angka = ''.join(random.choices(string.digits, k=5))
    id_booking = (f"{angka}") 
    return id_booking


@app.route('/schedule')
def get_schedule_id():
    if 'is_logged_in' in session :
        id_schedule = request.args.get('id_schedule')
        jml_seat = request.args.get('jml_seat')
        api_url = 'http://127.0.0.1:4000/get-schedule'
        api_data = {'schedule_id': id_schedule}
        print(api_data)
        response = requests.post(api_url, json=api_data) 
        print(response.status_code)
        if response.status_code == 200:
            data = response.json()['schedule']

            id_movie = data[0]['id_movie']
            id_theaters = data[0]['id_theaters']
            jam = data[0]['jam']
            studio = data[0]['studio']
            harga = str(data[0]['price'])

            info = (f"{id_movie}|{id_theaters}|{harga}|{jam}|{get_current_date()}")
            url = url_for('seat', booking=id_schedule, info=info, studio=studio, jml_seat=jml_seat)

            return redirect(url)  
        else:
            return redirect(url_for('home')) 
    else : 
        return redirect(url_for('login')) 

@app.route('/seat')
def seat():
    studio = int(request.args.get('studio'))
    if studio == 1 :
        return render_template('studio1.html')
    elif studio == 2 : 
        return render_template('studio2.html')
    elif studio == 3 : 
        return render_template('studio3.html')



@app.route('/movies-page/<id_movies>')
def movies(id_movies):
    api_url = f'http://127.0.0.1:4000/validate-movie/{id_movies}'
    response = requests.post(api_url) 

    if response.status_code == 200: 
        print('response.status_code')
        return render_template('movie-details.html', id_movies=id_movies)
    else: 
        abort(400)

@app.route('/theaters-list')
def theaters_list():
    return render_template('theaters-list.html')


    
@app.route('/playing')
def playing():
    return render_template('playing.html')



@app.route('/upcoming')
def upcoming():
    return render_template('upcoming.html')

@app.route('/theater', methods=['POST', 'GET'])
def theater():
    print(request.method)
    if request.method == "POST" : 
        jml_seat = request.form["selectTickets"]
        id_schedule = request.form["inpId"]
        return redirect(url_for('get_schedule_id', id_schedule=id_schedule, jml_seat=jml_seat))
    else : 
        return render_template('theater-detail.html')

# -------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------- D A S H B O A R D ---------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
@app.route('/dashboard')
def dashboard() : 
    if 'is_logged_in' in session and session['level_user'] != 3 :
        return render_template('/dashboard/dashboard.html')
    return render_template('/lain-lain/not-found.html')


@app.route('/dashboard/movies-list')
def movies_menu(): 
    if 'is_logged_in' in session and session['level_user'] != 3 :
        return render_template('dashboard/movies-menu.html')
    return render_template('/lain-lain/not-found.html')


@app.route('/dashboard/add-movies')
def add_movies(): 
    if 'is_logged_in' in session and session['level_user'] != 3 :
        return render_template('dashboard/add-movies.html')
    return render_template('/lain-lain/not-found.html')


@app.route('/dashboard/schedule-list')
def schedule_list(): 
    if 'is_logged_in' in session and session['level_user'] != 3 :   
        return render_template('dashboard/schedule-list.html')
    return render_template('/lain-lain/not-found.html')


@app.route('/dashboard/add-schedule')
def add_schedule() : 
    if 'is_logged_in' in session and session['level_user'] != 3 :   
        return render_template('/dashboard/add-schedule.html')
    return render_template('/lain-lain/not-found.html')



@app.route('/dashboard/theater')
def bioskop() : 
    if 'is_logged_in' in session and session['level_user'] != 3 :   
        return render_template('/dashboard/theater.html')
    return render_template('/lain-lain/not-found.html')



@app.route('/dashboard/daftar-transaksi')
def daftar_tranaski() : 
    if 'is_logged_in' in session and session['level_user'] != 3 :   
        return render_template('/dashboard/transaksi.html')
    return render_template('/lain-lain/not-found.html')



@app.route('/dashboard/add-carousel')
def add_carousel(): 
    if 'is_logged_in' in session and session['level_user'] == '1' :
        return render_template('dashboard/add-carousel.html')
    return render_template('/lain-lain/not-found.html')


@app.route('/dashboard/carousel')
def carousel():
    if 'is_logged_in' in session and session['level_user'] == '1' :
        return render_template('/dashboard/carousel-list.html')
    return render_template('/lain-lain/not-found.html')


@app.route('/dashboard/add-administrator')
def add_administrator() : 
    if 'is_logged_in' in session and session['level_user'] == '1' : 
        return render_template('/dashboard/add-administrator.html')
    return render_template('/lain-lain/not-found.html')



@app.route('/dashboard/administrator-list')
def administrator_list() : 
    if 'is_logged_in' in session and session['level_user'] == '1' : 
        return render_template('/dashboard/administrator-list.html')
    return render_template('/lain-lain/not-found.html')



@app.route('/dashboard/laporan-penjualan')
def laporan_penjualan() : 
    if 'is_logged_in' in session and session['level_user'] == '1' : 
        return render_template('/dashboard/laporan-penjualan.html')
    return render_template('/lain-lain/not-found.html')



@app.route('/daftar-transaksi', methods=["POST"])
def daftar_transaksi() : 
    if 'is_logged_in' in session and session['level_user'] != '3' : 
        api_url = 'http://127.0.0.1:4000/daftar-transaksi'

        if session['level_user'] == '2' :
            api_data = {'id_theaters' : session['id_theater']}
            response = requests.post(api_url, json=api_data)  
        else :
            api_data = {}
            response = requests.post(api_url, json=api_data)

        return response.json(),200



@app.route('/dashboard-data', methods=["POST"])
def dashboard_data() : 
    if 'is_logged_in' in session and session['level_user'] != '3' : 
        api_url = 'http://127.0.0.1:4000/penjualan-dashboard'

        if session['level_user'] == '2' :
            api_data = {'id_theaters' : session['id_theater']}
            response = requests.post(api_url, json=api_data)  
        else :
            api_data = {}
            response = requests.post(api_url, json=api_data)

        return response.json(),200



# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------- U S E R --------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
@app.route('/riwayat-transaksi')
def riwayat_transaksi() : 
    if 'is_logged_in' in session :
        return render_template('user/riwayat-transaksi.html')
    return render_template('/lain-lain/not-found.html')


@app.route('/account')
def profile() : 
    if 'is_logged_in' in session :
        id_user = session['user_id']
        return render_template('user/profile.html', id_user = id_user)
    return render_template('/lain-lain/not-found.html')



# -------------------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------- M I D T R A N S ----------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
# @app.route('/notification_handler', methods=['POST'])
# def notification_handeler() :
#     print('Notification Handler')
#     request_json = request.get_json()

#     api_url = 'http://127.0.0.1:4000/notification_handler'
#     response = requests.post(api_url, json=request_json)

#     if response.status_code == 200:
#         data = response.json() 

#     return jsonify(data)



@app.route('/notification_handler', methods=['POST'])
def notification_handler():
    print('Notification Handler')
    request_json = request.get_json()
    transaction_status_dict = core.transactions.notification(request_json)

    print(request_json)
    print('\n')
    print(request_json['va_numbers'])
    print('\n')


    order_id           = request_json['order_id']
    transaction_status = request_json['transaction_status']
    fraud_status       = request_json['fraud_status']
    transaction_json   = json.dumps(transaction_status_dict)

    summary = 'Transaction notification received. Order ID: {order_id}. Transaction status: {transaction_status}. Fraud status: {fraud_status}.<br>Raw notification object:<pre>{transaction_json}</pre>'.format(order_id=order_id,transaction_status=transaction_status,fraud_status=fraud_status,transaction_json=transaction_json)

    # [5.B] Handle transaction status on your backend
    # Sample transaction_status handling logic
    if transaction_status == 'capture':
        if fraud_status == 'challenge':
            # TODO set transaction status on your databaase to 'challenge'
            cur = mysql.connection.cursor() 
            cur.execute("UPDATE booking SET status = %s WHERE id_booking = %s",(transaction_status, order_id,))
            mysql.connection.commit() 

        elif fraud_status == 'accept':
            # TODO set transaction status on your databaase to 'success'
            cur = mysql.connection.cursor() 
            cur.execute("UPDATE booking SET status = %s WHERE id_booking = %s",(transaction_status, order_id,))
            mysql.connection.commit() 

    elif transaction_status == 'settlement':
        # TODO set transaction status on your databaase to 'success'
        cur = mysql.connection.cursor() 
        cur.execute("UPDATE booking SET status = %s WHERE id_booking = %s",('success', order_id,))
        mysql.connection.commit() 
        
    elif transaction_status == 'cancel' or transaction_status == 'deny' or transaction_status == 'expire':
        # TODO set transaction status on your databaase to 'failure'
        cur = mysql.connection.cursor() 
        cur.execute("UPDATE booking SET status = %s WHERE id_booking = %s",(transaction_status, order_id,))
        mysql.connection.commit() 
        
    elif transaction_status == 'pending':
        # TODO set transaction status on your databaase to 'pending' / waiting payment
        cur = mysql.connection.cursor() 
        cur.execute("UPDATE booking SET status = %s WHERE id_booking = %s",(transaction_status, order_id,))
        mysql.connection.commit() 

    elif transaction_status == 'refund':
        # TODO set transaction status on your databaase to 'refund'
        cur = mysql.connection.cursor() 
        cur.execute("UPDATE booking SET status = %s WHERE id_booking = %s",(transaction_status, order_id,))
        mysql.connection.commit() 

    # app.logger.info(summary)
    return jsonify(summary)



# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------


def get_current_date():
    current_date = datetime.now()
    current_date_str = current_date.strftime('%Y-%m-%d') 
    return current_date_str


@app.errorhandler(404)
@app.errorhandler(400)
@app.errorhandler(403)
def page_not_found(error):
    return render_template('/lain-lain/not-found.html')

@app.errorhandler(405)
def not_allow(error):
    return render_template('/lain-lain/method-not-allow.html')

@app.route('/not-found')
def not_found():
    return render_template('/lain-lain/method-not-allow.html')



@app.route('/dash-nav')
def dashnav():
    return render_template('/lain-lain/dash-nav.html')



if __name__== "__main__":
    app.run(debug=True)

    