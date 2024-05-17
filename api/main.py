from flask import Flask, render_template, session, request , redirect, url_for, flash, jsonify, send_file 
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt 
from midtransclient import Snap, CoreApi
from midtrans.paymentProcess import *
import requests
import os
import json
import random
import string
import qrcode


app = Flask(__name__)
CORS(app, origins=['http://127.0.0.1:5000'])

app.config['MYSQL_HOST'] = 'localhost'
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"]= ''
app.config["MYSQL_DB"] = 'cinema'
app.config["UPLOAD_FOLDER"] = 'static/images/'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

core = CoreApi(
    is_production=False,
    server_key= '<Your Server Key>',
    client_key='<Your Client Key>'
)


# -----------------------------------------------------------------
# ---------------------------- U S E R ---------------------------- 
# -----------------------------------------------------------------


@app.route('/login', methods=['POST'])
def login() : 
    try :
        email = request.json['email']
        password = request.json['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        result = cur.fetchone()

        if result:
            if not checkPassword(result[8], password) :
                return jsonify({'status': 'Error' , 'Massage' : 'Your credentials is invalid!' }),500
            user = [{"user_id" : result[0], 'username' : result[2], 'nama' : result[1], 'level_user' : result[11], 'id_theater' : result[12]}]
            return jsonify(user),200
        else : 
            return jsonify({"stauts" : 'Error', "message" : "Login Gagal!"}),500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500 



@app.route("/register", methods=["POST"])
def register():
    regis_data = request.json

    nama = regis_data["nama"]
    username = regis_data["username"]
    no_telp = regis_data["no_telp"]
    alamat = regis_data["alamat"]
    email = regis_data["email"]
    passwd = setPassword(regis_data["password"])
    gender = regis_data['gender']
    tanggal_lahir = regis_data['tanggal_lahir']
    level_user = '3'
    # image = 'default-profile.png'
    user_id = generate_user_id(tanggal_lahir)

    try : 
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (id_user, nama, username, email, tanggal_lahir, no_telp, gender, password, alamat, level_user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(user_id, nama, username, email, tanggal_lahir, no_telp, gender, passwd, alamat, level_user))
        mysql.connection.commit()
        return jsonify({'massage' : 'Register Success'}),200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500 



@app.route('/get-administrator', methods=['POST'])
def get_administrator() :
    cur = mysql.connection.cursor()
    cur.execute('SELECT u.*, t.nama_theaters FROM users u JOIN theaters t using(id_theaters) WHERE u.level_user="1" OR u.level_user="2"')
    result = cur.fetchall()
    cur.close()

    users = [{'id_user' : row[0], 'nama' : row[1], 'username' : row[2], 'email' : row[3], 'tanggal_lahir' : row[4], 'no_telp': row[5], 'alamat' : row[10], 'level_user' : row[11], 'id_theaters' : row[12], 'nama_theaters' : row[14]}   for row in result]

    return jsonify({'users' : users})


@app.route('/register-admin', methods=['POST'])
def register_admin() : 
    try : 
        data = request.json
        nama = data['nama']
        username = data['username']
        email = data['email']
        tanggal_lahir = data['tanggal_lahir']
        no_telp = data['no_telp']
        gender = data['gender']
        password = setPassword(data['password'])
        alamat = data['alamat']
        level_user = data['level_user']
        theater = data['theater']
        id_user = generate_user_id(tanggal_lahir)

        cur = mysql.connection.cursor() 
        cur.execute("INSERT INTO users (id_user, nama, username, email, tanggal_lahir, no_telp, gender, password, alamat, level_user, id_theaters) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (id_user, nama, username, email, tanggal_lahir, no_telp, gender, password, alamat, level_user, theater))
        mysql.connection.commit() 
        cur.close() 

        return jsonify({"Err" : False, 'message' : 'Berhasil Membuat Akun Admin!'}), 200
    except Exception as e : 
        error_message = str(e)
        print(error_message)
        return jsonify({'Err' : True, 'message' : error_message}), 500

# -----------------------------------------------------------------
# ------------------------- B O O K I N G -------------------------
# -----------------------------------------------------------------

@app.route('/save-booking', methods=['POST'])
def save_booking():
    booking_data = request.json
    date = datetime.now().strftime('%Y-%m-%d')
    user_id = booking_data['user_id']
    booking_id = generate_bookingId()
    id_schedule = booking_data['id_schedule']
    id_drink = booking_data['id_drink']
    id_seat = booking_data['id_seat']
    no_seat = booking_data['no_seat']
    total = booking_data['total']
    qr_code = generate_qr(booking_id)
    jml_seat = len(no_seat)

    cur = mysql.connection.cursor() 
    cur.execute("INSERT INTO booking (id_booking, id_user, id_schedule,  id_drink, tanggal_booking, jml_seat, total, qrcode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (booking_id, user_id, id_schedule, id_drink, date, jml_seat, total, qr_code))

    for seat, no in zip(id_seat, no_seat): 
        cur.execute("INSERT INTO detail_booking (id_booking, id_seat, no_seat) VALUES (%s, %s, %s)", (booking_id, seat, no))
    mysql.connection.commit() 

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qrcode', f'temp_qr_{booking_id}.png')
    send_file(f'temp_qr_{booking_id}.png',file_path, 'qrcode' )

    response = {'status': 'success', 'message': 'Berhasil Memesan!', 'booking_id' : booking_id}
    return jsonify(response), 200  



@app.route('/get-unavailable-Seat/<id_schedule>')
def unvailable_seat(id_schedule):
    date = datetime.now().strftime('%Y-%m-%d')
    cur = mysql.connection.cursor() 
    cur.execute("""SELECT db.id_seat
                FROM booking b
                JOIN detail_booking db using(id_booking)
                WHERE b.id_schedule=%s AND b.tanggal_booking=%s
                """, (id_schedule, date))
    result = cur.fetchall() 

    unavailable_seat = [row[0] for row in result]
    return jsonify(unavailable_seat)



@app.route('/generate_qr/<booking_id>')
def generate_qr(booking_id):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(booking_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    name = f"temp_qr_{booking_id}.png"
    img_temp_path = f"static/images/qrcode/{name}"
    img.save(img_temp_path)

    return name
    # return send_file(img_temp_path, mimetype='image/png', as_attachment=True)



@app.route('/get-transaction/<id_booking>', methods=['POST'])
def get_transaksi(id_booking):
    cur = mysql.connection.cursor() 
    cur.execute("""SELECT b.*, db.*, d.drink_name, s.id_movie, s.jam, m.title
                FROM booking b 
                JOIN detail_booking db using(id_booking)
                JOIN drink d using(id_drink)
                JOIN schedule s using(id_schedule)
                JOIN movies m using(id_movie)
                WHERE id_booking=%s
                """, (id_booking,))
    result = cur.fetchall() 

    # Menggabungkan data per id_booking
    booking_detail = {}
    for row in result:
        if row[0] not in booking_detail:
            booking_detail[row[0]] = {
                'id_booking': row[0],
                'id_user': row[1],
                'tanggal_booking': row[8],
                'status' : row[9],
                'metode_bayar' : row[10],
                'kode_bayar' : row[11],
                'batas_bayar' : format_datetime(row[12]),
                'jml_seat': row[3],
                'total': row[6],
                'qr_code': row[7],
                'id_schedule': row[2],  
                'no_seat': [],
                'minuman': row[17],
                'title' : row[20],
                'jam' : row[19],
                'id_movie' : row[18],
            }
        booking_detail[row[0]]['no_seat'].append(row[15])

    # Mengonversi set ke list untuk no_seat
    for booking in booking_detail.values():
        booking['no_seat'] = list(set(booking['no_seat']))

    id_user = result[0]
    update_pemabayaran(id_user[1])
    return jsonify({"booking_detail": list(booking_detail.values())})



@app.route('/daftar-transaksi', methods=["POST"])
def daftar_transaksi() :
    data = request.json
    cur = mysql.connection.cursor()

    if data :
        id_theaters = data['id_theaters']
        cur.execute("SELECT b.*, s.id_theaters FROM booking b JOIN schedule s using(id_schedule) WHERE b.status != ' ' AND s.id_theaters=%s ",(id_theaters,))
    else :
        cur.execute("SELECT * FROM booking WHERE status != ' ' ")
    result = cur.fetchall()

    transaksi = [{'id_booking' : row[0], "id_user" : row[1], "id_schedule" : row[2], "tanggal_booking" : row[4], 'jml_seat' : row[5], "total" : row[6], "status" : row[9], "metode_bayar" : row[10], "batas_bayar" : row[12]} for row in result]
    
    return jsonify({'transaksi' : transaksi}), 200



# -----------------------------------------------------------------
# --------------------------- M O V I E --------------------------- 
# -----------------------------------------------------------------


@app.route('/showing-movies', methods=['POST']) 
def show_movie():
    date = datetime.now().strftime('%Y-%m-%d')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT m.*, p.poster_name, (m.tanggal_rilis + INTERVAL 7 DAY)  AS'preorder_selesai' 
                FROM 
                    movies m
                INNER JOIN poster_image p USING(id_movie)
                WHERE tanggal_rilis <= %s AND m.status='aktif' OR preorder='ya' AND  m.tanggal_preorder >= %s AND m.status='aktif'
                ORDER BY m.tanggal_rilis DESC
                """,(date,date,))
    movies = cur.fetchall()
    cur.close()
    showing_movies = [{'id_movie' : row[0], 'title':row[1], 'sinopsis':row[2], 'sutradara':row[3], 'penulis' : row[4], 'produser':row[5], 'produksi' : row[6], 'cast': row[7], 'genre' : row[8], 'durasi' : row[9], 'rating' : row[10], 'tahun' : row[12], 'poster' : row[16], 'preorder' : row[14], 'tanggal_preorder' : row[15], 'preorder_selesai' : row[17]} for row in movies]

    return jsonify({'showing_movies' : showing_movies})



@app.route('/upcoming-movies', methods=['POST']) 
def upcoming_movie():
    date = datetime.now().strftime('%Y-%m-%d')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT m.*, p.poster_name 
                FROM 
                    movies m
                INNER JOIN 
                    poster_image p USING(id_movie)
                WHERE  m.tanggal_rilis > %s AND m.status='aktif' AND m.preorder !='ya' ORDER BY m.tanggal_rilis DESC 
                """,(date,))
    movies = cur.fetchall()
    cur.close()
    showing_movies = [{'id_movie' : row[0], 'title':row[1], 'sinopsis':row[2], 'sutradara':row[3], 'penulis' : row[4], 'produser':row[5], 'produksi' : row[6], 'cast': row[7], 'genre' : row[8], 'durasi' : row[9], 'rating' : row[10], 'tahun' : row[12], 'poster' : row[16]} for row in movies]

    return jsonify({'showing_movies' : showing_movies})



@app.route('/get-movie-detail/<id_movie>', methods=['POST'])
def movie_detail(id_movie):
    cur = mysql.connection.cursor() 
    cur.execute("SELECT m.*, p.poster_name FROM movies m JOIN poster_image p using(id_movie) WHERE id_movie=%s",(id_movie,))
    movies = cur.fetchone()
    
    movies_detail =[{'id_movie' : movies[0], 'title':movies[1], 'sinopsis':movies[2], 'sutradara':movies[3], 'penulis' : movies[4], 'produser':movies[5], 'produksi' : movies[6], 'cast': movies[7], 'genre' : movies[8], 'durasi' : movies[9], 'rating' : movies[10], 'tanggal_rilis' : movies[11],'tahun' : movies[12], 'poster' : movies[16], 'status' : movies[13]}]

    return jsonify({'movies' : movies_detail})



@app.route('/validate-movie/<id_movies>', methods=['POST'])
def validate_id_movies(id_movies):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM movies WHERE id_movie = %s", (id_movies,))
    count = cur.fetchone()[0]
    cur.close()
    if count:
        return '', 200
    else:
        return '', 404



@app.route('/add-movies', methods=["POST"])
def add_movies(): 
    try: 
        subfolder = 'poster'
        data = request.form
        gambar = request.files['poster']
        judul = data['judul']
        sinopsis = data['sinopsis']
        penulis = data['penulis']
        sutradara = data['sutradara']
        produser = data['produser']
        produksi = data['produksi']
        durasi = data['durasi']
        rating = data['rating']
        tanggal_rilis = data['tanggal_rilis']
        tahun = data['tahun']
        cast = data['cast']
        genre = data['genre']
        id_movie = generate_movie_id()

        image_filename = secure_filename(gambar.filename)
        save_image(gambar, subfolder)

        try : 
            cur = mysql.connection.cursor() 
            cur.execute("INSERT INTO movies (id_movie, title, sinopsis, sutradara, penulis, produser, produksi, cast, genre, durasi, rating, tanggal_rilis, tahun) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (id_movie, judul, sinopsis, sutradara, penulis, produser, produksi, cast, genre, durasi, rating, tanggal_rilis, tahun,))
            cur.execute("INSERT INTO poster_image (id_movie, poster_name) VALUES (%s, %s)", (id_movie, image_filename))
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            error_message = str(e)
            print(error_message)



        response = {'status': 'success', 'message': 'Berhasil Menyimpan Data Film!'}
        return jsonify(response), 200 
     
    except Exception as e:
        error_message = str(e)
        response = {'status': 'error', 'message': 'Gagal Mengubah Produk', 'error': error_message}
        return jsonify(response), 500 



@app.route('/get-all-movies', methods=["POST"])
def all_movies() : 
    cur = mysql.connection.cursor() 
    cur.execute("SELECT m.*, p.poster_name FROM movies m JOIN poster_image p using(id_movie) ORDER BY tanggal_rilis DESC")
    result = cur.fetchall() 

    movies = [{'id_movie' : row[0], 'title' : row[1],'sinopsis' : row[2], 'sutradara' : row[3], 'penulis' : row[4], 'produser' : row[5], 'produksi' : row[6], 'cast' : row[7], 'genre' : row[8], 'durasi' : row[9], 'rating' : row[10], 'tanggal_rilis' : row[11], 'tahun' : row[12], 'poster' : row[16], 'status' : row[13], 'preorder' : row[14]} for row in result]

    

    return jsonify({'movies' : movies}),200



@app.route('/delete-movie/<id_movie>', methods=['POST'])
def delete_movie(id_movie) :
    cur = mysql.connection.cursor() 
    cur.execute('DELETE FROM movies WHERE id_movie =%s', (id_movie))
    mysql.connection.commit()
    cur.close() 

    return jsonify({"Err" : False, "Message" : "Success Menghapus Film!"}), 200



@app.route('/update-movie', methods=['POST'])
def update_movie() :
    try :
        cur = mysql.connection.cursor() 
        subfolder = 'poster'
        data = request.form
        id_movie = data['id_movie']
        judul = data['title']
        sinopsis = data['sinopsis']
        penulis = data['penulis']
        sutradara = data['sutradara']
        produser = data['produser']
        produksi = data['produksi']
        durasi = data['durasi']
        rating = data['rating']
        tanggal_rilis = data['tanggal_rilis']
        tahun = data['tahun']
        cast = data['cast']
        genre = data['genre']

        if 'poster' in request.files: 
            gambar = request.files['poster']

            image_filename = secure_filename(gambar.filename)
            save_image(gambar, subfolder)

            cur.execute("UPDATE poster_image SET poster_name=%s WHERE id_movie=%s", (image_filename, id_movie)) 

        tanggal_preorder_on_rilis_change(id_movie, tanggal_rilis)
        cur.execute("UPDATE movies set title=%s, sinopsis=%s, sutradara=%s, penulis=%s, produser=%s, produksi=%s, cast=%s, genre=%s, durasi=%s, rating=%s, tanggal_rilis=%s, tahun=%s WHERE id_movie=%s", (judul, sinopsis, sutradara, penulis, produser, produksi, cast, genre, durasi, rating, tanggal_rilis, tahun, id_movie)) 
        mysql.connection.commit() 
        cur.close() 

        return jsonify({'Err' : False, 'message' : 'Berhasil Mengubah Data Film!'}), 200
    
    except Exception as e :
        error_message = str(e)
        return jsonify({'Err' : True, 'message' : error_message}), 500



@app.route('/update-status-movie', methods=["POST"])
def updateStatusMovie() :
    try :
        cur = mysql.connection.cursor() 
        data = request.json 
        id_movie = data['id_movie']
        status = data['status']
        print(data)

        try :
            cur.execute('UPDATE movies SET status=%s WHERE id_movie=%s', (status, id_movie))
            mysql.connection.commit()
            cur.close()
        except Exception as e :
            error_message = str(e)  

        return jsonify({'Err' : False, 'message' : 'Berhfasil Update' }), 200

    except Exception as e :
        error_message = str(e)
        print(error_message)
        return jsonify({'Err' : True, 'message' : error_message }), 500
    


@app.route('/add-preorder', methods=["POST"])
def add_preorder() :
    try :
        cur = mysql.connection.cursor() 
        data = request.json 
        id_movie = data['id_movie']
        preorder = data['preorder']
        print(data)

        update_tanggal_preorder(id_movie, preorder)
        try :
            cur.execute('UPDATE movies SET preorder=%s WHERE id_movie=%s', (preorder, id_movie))
            mysql.connection.commit()
            cur.close()
        except Exception as e :
            error_message = str(e)  

        return jsonify({'Err' : False, 'message' : 'Berhfasil Update' }), 200

    except Exception as e :
        error_message = str(e)
        print(error_message)
        return jsonify({'Err' : True, 'message' : error_message }), 500
    

# -----------------------------------------------------------------
# ------------------------ S C H E D U L E ------------------------ 
# -----------------------------------------------------------------

@app.route('/get-schedule', methods=['GET','POST'])
def get_schedule(): 
    data = request.json
    schedule_id = data['schedule_id']
    cur = mysql.connection.cursor()
    cur.execute("""SELECT s.*, m.*, t.nama_theaters 
                FROM schedule s
                INNER JOIN movies m using(id_movie)
                INNER JOIN theaters t using(id_theaters)
                WHERE id_schedule=%s""",(schedule_id,))
    result = cur.fetchone()
    price = get_price(result[2])

    schedule = [{'id_schedule' : result[0], 'id_movie' : result[1], 'id_theaters' : result[2], 'jam' : result[4], 'studio' : result[5], 'price' : price}]
    schedule_detail = [{'id_schedule' : result[0], 'id_movie' : result[1], 'id_theaters' : result[2], 'tanggal_schedule' : result[3 ],'jam' : result[4], 'studio' : result[5], 'title' : result[7], 'nama_theaters' : result[22], 'price' : price}]
    
    return jsonify({'schedule' : schedule, 'schedule_detail' : schedule_detail}),200


@app.route('/schedule-detail/<id_schedule>', methods=['GET','POST'])
def schedule_detail(id_schedule): 
    cur = mysql.connection.cursor()
    cur.execute("""SELECT s.*, m.*, t.nama_theaters 
                FROM schedule s
                INNER JOIN movies m using(id_movie)
                INNER JOIN theaters t using(id_theaters)
                WHERE id_schedule=%s""",(id_schedule,))
    result = cur.fetchone()

    price = get_price(result[2])

    schedule = [{'id_schedule' : result[0], 'id_movie' : result[1], 'id_theaters' : result[2], 'jam' : result[4], 'studio' : result[5], 'price' : price}]
    schedule_detail = [{'id_schedule' : result[0], 'id_movie' : result[1], 'id_theaters' : result[2], 'jam' : result[4], 'studio' : result[5], 'title' : result[7], 'nama_theaters' : result[22], 'price' : price}]
    
    return jsonify({'schedule' : schedule, 'schedule_detail' : schedule_detail}),200


@app.route('/get-schedule-movie/<id_movies>', methods=['POST'])
def schedule_movie(id_movies):
    date = datetime.now().strftime('%Y-%m-%d')
    cur = mysql.connection.cursor() 
    cur.execute("""SELECT s.*, t.nama_theaters, m.tanggal_rilis, m.preorder, m.tanggal_preorder
                FROM schedule s
                JOIN theaters t USING (id_theaters)
                JOIN movies m USING (id_movie)
                WHERE id_movie=%s AND 
                (tanggal_schedule = %s OR tanggal_schedule >= m.tanggal_preorder AND tanggal_schedule <= m.tanggal_rilis + INTERVAL 7 DAY AND tanggal_schedule >= %s)
                ORDER BY tanggal_schedule ASC
                """,
                (id_movies, date, date))
    result = cur.fetchall()
    cur.close()


    movie_schedule = [{'id_schedule' : row[0], 'id_movie' : row[1], 'id_theaters' : row[2], 'jam':row[4], 'studio' : row[5], 'nama_theaters' : row[6], 'price' : get_price(row[2]), 'tanggal' : row[3]} for row in result]

    return jsonify({'movie_schedule' : movie_schedule}),200



@app.route('/schedule-list', methods=['GET','POST'])
def schedule_list(): 
    date = datetime.now().strftime('%d-%m-%Y')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT s.*, m.title, t.nama_theaters
                FROM  schedule s 
                JOIN movies m using(id_movie)
                JOIN theaters t using(id_theaters) 
                ORDER BY tanggal_schedule DESC
                """,)
    result = cur.fetchall()


    schedule = [{'id_schedule' : row[0], 'tanggal':row[3], 'nama_theaters' : row[7], 'title' : row[6],'jam' : row[4], 'studio' : row[5]} for row in result]
    
    return jsonify({'data' : schedule}),200



@app.route('/schedule-list-theater/<id_theaters>', methods=['GET','POST'])
def schedule_list_theater(id_theaters): 
    date = datetime.now().strftime('%d-%m-%Y')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT s.*, m.title, t.nama_theaters
                FROM  schedule s 
                JOIN movies m using(id_movie)
                JOIN theaters t using(id_theaters) 
                WHERE id_theaters=%s 
                ORDER BY tanggal_schedule DESC
                """, (id_theaters,))
    result = cur.fetchall()


    schedule = [{'id_schedule' : row[0], 'tanggal':row[3], 'nama_theaters' : row[7], 'title' : row[6],'jam' : row[4], 'studio' : row[5]} for row in result]
    
    return jsonify({'data' : schedule}),200



@app.route('/get-all-theaters', methods=['POST'])
def all_theater() : 
    cur = mysql.connection.cursor() 
    cur.execute("SELECT * FROM theaters")
    result = cur.fetchall()

    theaters = [{'id_theaters' : row[0], 'nama_theaters' : row[1], 'alamat_theaters' : row[2], 'no_telp' : row[3], 'region' : row[5]} for row in result]

    return jsonify({'theaters' : theaters}), 200



@app.route('/add-schedule', methods=["POST"])
def add_schedule() : 
    try : 
        data = request.json
        id_movie = data['id_movie']
        id_theaters = data['id_theater']
        tanggal = data['tanggal']
        jam = data['jam']
        studio = data['studio']
        id_schedule = generate_id_schedule(id_theaters)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO schedule (id_schedule, id_movie, id_theaters, tanggal_schedule, jam, studio) VALUES (%s, %s, %s, %s, %s, %s)",(id_schedule, id_movie, id_theaters, tanggal, jam, studio))
        mysql.connection.commit() 

        return jsonify({'Err' : False, 'message' : 'Berhasil Menambahkan Jadwal!'}), 200
    except Exception as e : 
        error_message = str(e)
        print(error_message)
        return jsonify({'Err': True ,'message' : error_message}), 500



# @app.route('/get-theater-schedule/<id_theater>', methods=['POST'])
# def theater_schedule(id_theater) :
#     date = datetime.now().strftime('%Y-%m-%d')
#     cur = mysql.connection.cursor()
#     cur.execute("""SELECT s.*, m.*, t.nama_theaters, p.poster_name
#                 FROM schedule s
#                 INNER JOIN movies m using(id_movie)
#                 INNER JOIN theaters t using(id_theaters)
#                 INNER JOIN poster_image p using(id_movie)
#                 WHERE id_theaters=%s AND (s.tanggal_schedule = %s OR tanggal_schedule >= m.tanggal_preorder AND s.tanggal_schedule <= m.tanggal_rilis + INTERVAL 7 DAY)
#                 ORDER BY 
#                 CAST(SUBSTRING_INDEX(jam, ':', 1) AS UNSIGNED),
#                 CAST(SUBSTRING_INDEX(jam, ':', -1) AS UNSIGNED)
#                 """,(id_theater, date,))
#     result = cur.fetchall()
#     cur.close()
#     # schedule = [{'id_schedule' : row[0], 'id_movie' : row[1], 'id_theaters' : row[2], 'jam' : row[4], 'studio' : row[5], 'price' : get_price(row[2]), 'title' : row[7], 'tanggal' : row[3] } for row in result]

#     schedule_dict = {}
#     for row in result:
#         key = (row[1], row[2])  
#         if key in schedule_dict:
#             schedule_dict[key]['jam'].append(row[4])
#         else:
#             schedule_dict[key] = {
#                 'id_schedule': row[0],
#                 'id_movie': row[1],
#                 'id_theaters': row[2],
#                 'studio': row[5],
#                 'price': get_price(row[2]),
#                 'title': row[7],
#                 'tanggal': row[3],
#                 'jam': [row[4]],
#                 'genre': row[14],
#                 'durasi': row[15],
#                 'rating': row[16],
#                 'poster': row[20],
#                 'nama_theaters': row[19]
#             }

#     schedule = list(schedule_dict.values())
    
#     for x in schedule : 
#         print(x)

#     return jsonify({'schedule' : schedule}), 200



@app.route('/get-theater-schedule/<id_theater>', methods=['POST'])
def theater_schedule(id_theater) :
    date = datetime.now().strftime('%Y-%m-%d')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT s.*, m.*, t.nama_theaters, p.poster_name
                FROM schedule s
                INNER JOIN movies m using(id_movie)
                INNER JOIN theaters t using(id_theaters)
                INNER JOIN poster_image p using(id_movie)
                WHERE id_theaters=%s AND (s.tanggal_schedule = %s OR tanggal_schedule >= m.tanggal_preorder AND s.tanggal_schedule <= m.tanggal_rilis + INTERVAL 7 DAY)
                ORDER BY 
                CAST(SUBSTRING_INDEX(jam, ':', 1) AS UNSIGNED),
                CAST(SUBSTRING_INDEX(jam, ':', -1) AS UNSIGNED),
                tanggal_schedule ASC
                """,(id_theater, date,))
    result = cur.fetchall()
    cur.close()


    schedule_dict = {}
    for row in result:
        key = (row[1], row[2])  
        if key in schedule_dict:
            schedule_dict[key]['id_schedule'].append(row[0])
            schedule_dict[key]['jadwal'].append({'id_schedule' : row[0], 'tanggal' : row[3], 'jam' : row[4]})
        else:
            
            schedule_dict[key] = {
                'id_movie': row[1],
                'id_theaters': row[2],
                'studio': row[5],
                'price': get_price(row[2]),
                'title': row[7],
                'id_schedule' : [row[0]],
                'jadwal': [{'id_schedule' : row[0], 'tanggal' : row[3], 'jam' : row[4]}],
                'genre': row[14],
                'durasi': row[15],
                'rating': row[16],
                'poster': row[23],
                'nama_theaters': row[19]
            }

    schedule = list(schedule_dict.values())

    print(schedule_dict)
    
    
    return jsonify({'schedule' : schedule}), 200



@app.route('/delete-schedule', methods=['POST'])
def delete_schedule() : 
    try : 
        data = request.json 
        id_schedule = data['id_schedule']
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM schedule WHERE id_schedule=%s", (id_schedule,))
        mysql.connection.commit() 

        return jsonify({"Err" : False, "message" : "Berhasil Menghapus Schedule!"})
    except Exception as e : 
        error_message = str(e)
        return jsonify({"Err" : True, "message" : error_message })



@app.route('/update-schedule', methods=['POST'])
def update_schedule() : 
    try : 
        data = request.json 
        id_schedule = data['id_schedule']
        tanggal = data['tanggal']
        jam = data['jam']
        studio = data['studio']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE schedule SET tanggal_schedule=%s, jam=%s, studio=%s   WHERE id_schedule=%s", (tanggal, jam, studio, id_schedule))
        mysql.connection.commit() 

        return jsonify({"Err" : False, "message" : "Berhasil Mengubah Schedule!"})
    except Exception as e : 
        error_message = str(e)
        return jsonify({"Err" : True, "message" : error_message })



@app.route('/check-schedule', methods=['POST'])
def check_schedule():
    try : 
        cur = mysql.connection.cursor()

        data = request.json
        tanggal_schedule = data['tanggal_schedule']
        jam = data['jam']
        studio = data['studio']
        id_movie = data['id_movie']
        id_theaters = data['id_theaters']

        cur.execute(f'SELECT durasi FROM movies WHERE id_movie="{id_movie}"')
        durasiFilm = cur.fetchone()[0]

    
        waktu_mulai = datetime.strptime(jam, "%H:%M") # Ini jam jadwal yang mau ditambahin
        selesai_film = waktu_mulai + timedelta(minutes=durasiFilm) # ini jam selesai jadwal

        cur.execute(""" 
                        SELECT s.id_movie, m.durasi, s.jam
                        FROM schedule s 
                        JOIN movies m ON s.id_movie = m.id_movie 
                        WHERE s.studio = %s AND s.tanggal_schedule = %s AND s.id_theaters=%s
                        """, (studio, tanggal_schedule, id_theaters))
        jadwal_info = cur.fetchall()

        for id_movie, durasi, jam_mulai in jadwal_info:
            waktu_mulai_jadwal = datetime.strptime(jam_mulai, "%H:%M") - timedelta(minutes=15) # ini jam jadwal yang ditabrak
            waktu_selesai = waktu_mulai_jadwal + timedelta(minutes=durasi) + timedelta(minutes=15) # ini jam selesai jadwal  yang ditabrak


            if (waktu_mulai >= waktu_mulai_jadwal and waktu_mulai <= waktu_selesai) or (selesai_film >= waktu_mulai_jadwal and waktu_mulai <= waktu_selesai):
                return jsonify(True), 200

            
        cur.close()
        return jsonify(False), 200
    except Exception as e :
        error_message = str(e)
        return jsonify({'Err' : True, 'message' : error_message}), 500



# -----------------------------------------------------------------
# --------------------------- D R I N K --------------------------- 
# -----------------------------------------------------------------

@app.route('/get-drink', methods=['POST'])
def get_drink():
    cur = mysql.connection.cursor() 
    cur.execute("SELECT * FROM drink")
    drink = cur.fetchall() 

    drink = [{'id_drink' : row[0], 'drink_name' : row[1], 'image_drink' : row[2]} for row in drink]

    return jsonify({'drink' : drink})



# -----------------------------------------------------------------
# ------------------------ T H E A T E R S ------------------------ 
# -----------------------------------------------------------------

@app.route('/theaters-list/<region>', methods=['POST'])
def theaters_list(region):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM theaters WHERE region =%s", (region,))
    result = cur.fetchall()
    cur.close()

    theaters = [{ "theaters_id" : row[0] ,"nama_theaters" : row[1], 'alamat' : row[2], 'no_telp' : row[3], 'price1' : row[4], 'price2' : row[5], 'price3' : row[6]} for row in result]

    return jsonify({'bioskop' : theaters})


@app.route('/get-theater/<id_theater>', methods=['POST'])
def get_theater(id_theater):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM theaters WHERE id_theaters =%s", (id_theater,))
    result = cur.fetchall()
    cur.close()

    theaters = [{ "theaters_id" : row[0] ,"nama_theaters" : row[1], 'alamat' : row[2], 'no_telp' : row[3], 'price1' : row[4], 'price2' : row[5], 'price3' : row[6]} for row in result]

    return jsonify({'bioskop' : theaters})

@app.route('/theaters-all', methods=['POST'])
def theaters_all():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM theaters")
    result = cur.fetchall()
    cur.close()

    theaters = [{ "theaters_id" : row[0] ,"nama_theaters" : row[1], 'alamat' : row[2], 'no_telp' : row[3], 'price1' : row[4], 'price2' : row[5], 'price3' : row[6]} for row in result]

    return jsonify({'bioskop' : theaters})



@app.route('/delete-theater/<id_theater>', methods=['POST'])
def delete_theater(id_theater) :
    try :
        cur = mysql.connection.cursor() 
        cur.execute("DELETE FROM theaters WHERE id_theaters=%s", (id_theater))
        mysql.connection.commit() 
        cur.close() 

        return jsonify({'Err' : False, 'Message' : 'Berhasil Menghapus Theater!'}), 200
    except Exception as e :
        error_message = str(e)
        return jsonify({'Err' : True, 'message' : error_message}),500

# -----------------------------------------------------------------
# ----------------------- C A R O U S E L ------------------------- 
# -----------------------------------------------------------------

@app.route('/add-carousel', methods=['POST'])
def add_carousel() :
    try:
        subfolder = "carousel"
        images = request.files.getlist('images[]')
        titles = request.form.getlist('titles[]')

        for i in range(len(images)): 
            image = images[i]
            title = titles[i]
            image_filename = image.filename

            cur = mysql.connection.cursor() 
            cur.execute("INSERT INTO carousel (nama_carousel, image_carousel) VALUES (%s, %s)", (title, image_filename))
            mysql.connection.commit()

            save_image(image, subfolder)

        return jsonify({'message' : 'success'}), 200
    except Exception as e :
        error_message = str(e)
        print(error_message)
        return jsonify({'message' : error_message}), 500



@app.route('/get-carousel', methods=['POST'])
def get_carousel() : 
    cur = mysql.connection.cursor() 
    cur.execute('SELECT * FROM carousel')
    result = cur.fetchall() 

    carousel = [{'id_carousel' : row[0], 'nama_carousel' : row[1], 'image_carousel': row[2]} for row in result]

    return jsonify({'carousel' : carousel})



@app.route('/delete-carousel/<int:id>', methods=['POST'])
def delete_carousel(id) : 
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM carousel WHERE id_carousel=%s', (id,))
    mysql.connection.commit() 
    cur.close()

    return jsonify({'Message' : "Success Delete Carousel!"}), 200



# -----------------------------------------------------------------
# --------------------------- U S E R ----------------------------- 
# -----------------------------------------------------------------

@app.route('/get-riwayat-transaksi/<id_user>', methods=['POST'])
def get_riwayat(id_user) :
    cur = mysql.connection.cursor() 
    cur.execute("""SELECT b.*, db.*, d.drink_name, s.id_movie, s.jam, m.title, t.nama_theaters
                FROM booking b 
                JOIN detail_booking db using(id_booking)
                JOIN drink d using(id_drink)
                JOIN schedule s using(id_schedule)
                JOIN movies m using(id_movie)
                JOIN theaters t using(id_theaters)
                WHERE id_user=%s
                ORDER BY tanggal_booking DESC
                """, (id_user,))
    result = cur.fetchall() 

    booking_detail = {}
    for row in result:
        if row[0] not in booking_detail:
            booking_detail[row[0]] = {
                'id_booking': row[0],
                'id_user': row[1],
                'tanggal_booking': row[8],
                'jml_seat': row[5],
                'total': row[6],
                'qr_code': row[7],
                'status' : row[9].capitalize(),
                'id_schedule': row[2],  
                'no_seat': [],
                'drink': row[14],
                'title' : row[20],
                'jam' : row[19],
                'theaters' : row[21]
            }
        booking_detail[row[0]]['no_seat'].append(row[12])

    # Mengonversi set ke list untuk no_seat
    for booking in booking_detail.values():
        booking['no_seat'] = list(set(booking['no_seat']))

    update_pemabayaran(id_user)
    return jsonify({"riwayat": list(booking_detail.values())})



@app.route('/get-profile', methods=["POST"])
def get_profile():
    try : 
        cur = mysql.connection.cursor()
        data = request.json
        id_user = data['id_user']

        cur.execute(f'SELECT * FROM users WHERE id_user="{id_user}"')
        users = cur.fetchone() 
        cur.close()

        user = {'id_user' : users[0], 'nama' : users[1], 'username' : users[2], 'email' : users[3], 'tanggal_lahir' : users[4], 'no_telp' : users[5], 'gender' : users[6], 'alamat': users[10], 'profile_image' : users[12]}

        return jsonify(user),200

    except Exception as e :
        error_message = str(e)
        return jsonify({'Err' : True, 'message' : error_message}),500
    


@app.route('/update-profile', methods=['POST'])
def update_profile() :
    try : 
        subfolder = 'profile_image'
        cur = mysql.connection.cursor() 
        data = request.form
        nama = data['nama']
        alamat = data['alamat']
        gender = data['gender']
        tanggal_lahir = data['tanggal_lahir']
        id_user = data['id_user']


        if 'profile_image' in request.files: 
            gambar = request.files['profile_image']

            image_filename = secure_filename(gambar.filename)
            save_image(gambar, subfolder)

            cur.execute("UPDATE users SET profile_image=%s WHERE id_user=%s", (image_filename, id_user))

        cur.execute(f"UPDATE users SET nama='{nama}', alamat='{alamat}', gender='{gender}', tanggal_lahir='{tanggal_lahir}' WHERE id_user='{id_user}'")
        mysql.connection.commit()
        cur.close()
  
        return jsonify({'Err' : False, 'message' : 'Update Success!'}),200

    except Exception as e :
        error_message = str(e)
        return jsonify({'Err' : True, 'message' : error_message}),500

# -----------------------------------------------------------------
# ---------------------- S T A T I S T I K ------------------------ 
# -----------------------------------------------------------------

@app.route('/penjualan', methods=['POST'])
def penjualan() :
    days = datetime.now().strftime('%d')
    month = datetime.now().strftime('%m')
    cur = mysql.connection.cursor()
    cur.execute("""
                SELECT 
                    SUM(CASE WHEN DAY(tanggal_booking) = DAY(NOW()) THEN 1 ELSE 0 END) AS hari_ini,
                    SUM(CASE WHEN MONTH(tanggal_booking) = MONTH(NOW()) THEN 1 ELSE 0 END) AS bulan_ini
                FROM 
                    booking
                WHERE 
                    MONTH(tanggal_booking) = MONTH(NOW())
                    AND YEAR(tanggal_booking) = YEAR(NOW())
                    AND status='success';
                """)
    penjualan = cur.fetchone()
    cur.close()

    sales = {
        'hari_ini': penjualan[0],
        'bulan_ini': penjualan[1]
    }

    return jsonify(sales),200



@app.route('/penjualan-dashboard', methods=['POST'])
def penjualan_dashboard() :
    data = request.json
    cur = mysql.connection.cursor()

    if data : 
        id_theaters = data['id_theaters']
        cur.execute("""
                    SELECT 
                        SUM(CASE WHEN DATE(b.tanggal_booking) = DATE(NOW()) THEN 1 ELSE 0 END) AS hari_ini,
                        SUM(CASE WHEN MONTH(b.tanggal_booking) = MONTH(NOW()) AND YEAR(tanggal_booking) = YEAR(NOW()) THEN 1 ELSE 0 END) AS bulan_ini,
                        SUM(CASE WHEN DATE(b.tanggal_booking) = DATE(NOW()) THEN total ELSE 0 END) AS total_hari_ini,
                        SUM(CASE WHEN MONTH(b.tanggal_booking) = MONTH(NOW()) AND YEAR(tanggal_booking) = YEAR(NOW()) THEN total ELSE 0 END) AS total_bulan_ini
                    FROM 
                        booking b 
                    JOIN 
                        schedule s using(id_schedule)
                    WHERE 
                        s.id_theaters = %s AND
                        MONTH(tanggal_booking) = MONTH(NOW())
                        AND YEAR(tanggal_booking) = YEAR(NOW())
                        AND status='success';
                    """, (id_theaters,))
    else : 
         cur.execute("""
                    SELECT 
                        SUM(CASE WHEN DATE(tanggal_booking) = DATE(NOW()) THEN 1 ELSE 0 END) AS hari_ini,
                        SUM(CASE WHEN MONTH(tanggal_booking) = MONTH(NOW()) AND YEAR(tanggal_booking) = YEAR(NOW()) THEN 1 ELSE 0 END) AS bulan_ini,
                        SUM(CASE WHEN DATE(tanggal_booking) = DATE(NOW()) THEN total ELSE 0 END) AS total_hari_ini,
                        SUM(CASE WHEN MONTH(tanggal_booking) = MONTH(NOW()) AND YEAR(tanggal_booking) = YEAR(NOW()) THEN total ELSE 0 END) AS total_bulan_ini
                    FROM 
                        booking
                    WHERE 
                        status = 'success'
                        AND YEAR(tanggal_booking) = YEAR(NOW())
                        AND MONTH(tanggal_booking) = MONTH(NOW());
                    """)
    penjualan = cur.fetchone()
    cur.close()

    sales = {
        'hari_ini': penjualan[0],
        'bulan_ini': penjualan[1],
        'total_hari ini' : penjualan[2],
        'total_bulan ini' : penjualan[3]
    }

    return jsonify(sales),200



@app.route('/get-profile-image/<id_user>', methods=['post'])
def get_profile_image(id_user) : 
    cur = mysql.connection.cursor() 
    cur.execute('SELECT profile_image FROM users WHERE id_user=%s', (id_user,))
    profile_image = cur.fetchone()[0]
    cur.close()

    return jsonify(profile_image), 200



@app.route('/penjualan-bulanan', methods=["POST"])
def monthly_sale() : 
    cur = mysql.connection.cursor() 
    cur.execute("""
                SELECT 
                    MONTHNAME(tanggal_booking) AS 'bulan', 
                    COUNT(*) AS 'jumlah transaksi', 
                    SUM(jml_seat) AS 'seat terjual', 
                    SUM(total) AS 'totalAmount',
                    AVG(total) / DAY(LAST_DAY(tanggal_booking))
                FROM
                    booking 
                WHERE status='success' AND YEAR(tanggal_booking) = YEAR(CURDATE())
                GROUP BY MONTHNAME(tanggal_booking)""")
    result = cur.fetchall()

    cur.execute("""
                SELECT 
                COUNT(*) AS 'transaksi tahun ini',
                SUM(CASE WHEN MONTH(tanggal_booking) = MONTH(NOW()) THEN 1 ELSE 0 END) AS 'transaksi_bulan_ini',
                SUM(CASE WHEN MONTH(tanggal_booking) = MONTH(NOW()) THEN total ELSE 0 END) AS 'total_bulan_ini',
                SUM(total) as 'total_tahun_ini'
                FROM 
                booking
                WHERE status='success'
                """)
    statis = cur.fetchall()[0]
    

    bulan_sekarang = datetime.now().month
    bulan_tahun_ini = [datetime(2024, i, 1).strftime('%B') for i in range(1, bulan_sekarang + 1)]

    data_bulanan = {bulan: {'jumlah_transaksi': 0, 'seat_terjual': 0, 'total_amount': 0, 'avg_bulanan' : 0} for bulan in bulan_tahun_ini}

    for row in result:
        bulan = row[0]  
        data_bulanan[bulan] = {
            'jumlah_transaksi': row[1],  
            'seat_terjual': row[2],       
            'total_amount': row[3],      
            'avg_bulanan': row[4],      
        }

    monthly = [{'bulan': bulan, **data} for bulan, data in data_bulanan.items()]

    return jsonify({'monthly' : monthly, 'transaksi_tahunan' : statis[0], 'transaksi_bulanan' : statis[1], 'total_bulan_ini' : statis[2], 'total_tahun_ini' : statis[3]}),200



@app.route('/statistik-theater/<id_theater>', methods=["POST"])
def statistik_theater(id_theater) :
    cur = mysql.connection.cursor() 
    cur.execute("""
                SELECT 
                    MONTHNAME(b.tanggal_booking) AS 'bulan', 
                    COUNT(*) AS 'jumlah transaksi', 
                    SUM(b.jml_seat) AS 'seat terjual', 
                    SUM(b.total) AS 'totalAmount',
                    AVG(b.total) / DAY(LAST_DAY(b.tanggal_booking))
                FROM
                    booking b 
                JOIN
                    schedule s using(id_schedule)
                WHERE s.id_theaters=%s AND b.status='success' AND YEAR(b.tanggal_booking) = YEAR(CURDATE())
                GROUP BY MONTHNAME(tanggal_booking)""", (id_theater,))
    result = cur.fetchall()

    bulan_sekarang = datetime.now().month
    bulan_tahun_ini = [datetime(2024, i, 1).strftime('%B') for i in range(1, bulan_sekarang + 1)]

    data_bulanan = {bulan: {'jumlah_transaksi': 0, 'seat_terjual': 0, 'total_amount': 0, 'avg_bulanan' : 0} for bulan in bulan_tahun_ini}

    for row in result:
        bulan = row[0]  
        data_bulanan[bulan] = {
            'jumlah_transaksi': row[1],  
            'seat_terjual': row[2],       
            'total_amount': row[3],      
            'avg_bulanan': row[4],      
        }

    monthly = [{'bulan': bulan, **data} for bulan, data in data_bulanan.items()]

    return jsonify({'monthly' : data_bulanan})



@app.route('/pendapatan-theater', methods=["POST"])
def pendapatan_theater():
    cur = mysql.connection.cursor() 
    cur.execute("""
                SELECT 
                    t.nama_theaters,
                    COALESCE(SUM(b.total), 0) as pendapatan_bulan_ini,
                    COALESCE(SUM(b.jml_seat), 0) as pendapatan_bulan_ini
                FROM
                    theaters t
                LEFT JOIN 
                    schedule s ON t.id_theaters = s.id_theaters
                LEFT JOIN 
                    booking b ON s.id_schedule = b.id_schedule AND b.status = 'success'
                GROUP BY 
                    t.nama_theaters;
                """)
    result = cur.fetchall()

    summary = [{'nama_theater' : row[0], 'summary' : row[1], 'viewer' : row[2]} for row in result]

    return jsonify(summary), 200



@app.route('/penonton-film', methods=["POST"])
def penonton_film():
    cur = mysql.connection.cursor() 
    cur.execute("""
        SELECT 
            m.id_movie, m.title,
            IFNULL(SUM(b.jml_seat), 0) AS 'jumlah penonton'
        FROM 
            movies m 
        LEFT JOIN 
            schedule s USING (id_movie) 
        LEFT JOIN 
            booking b USING (id_schedule)
        WHERE 
            b.status='success' OR b.status IS NULL AND m.status = 'aktif'
        GROUP BY 
            m.id_movie
    """)
    result = cur.fetchall()
    cur.close()

    movies = {}
    for row in result:
        movie_id = row[0]
        movies[movie_id] = {
            'title': row[1],
            'jml_penonton': row[2]
        }

    movie = [{'id_movie': id_movie, **data} for id_movie, data in movies.items()]

    return jsonify({'penonton' : movie}), 200



@app.route('/most-movie', methods=["POST"])
def most_movie() :
    cur = mysql.connection.cursor() 
    cur.execute("""
                SELECT
                    MAX(total_seat) AS jml_penonton,
                    title,
                    poster_name
                FROM
                    (
                        SELECT
                            SUM(b.jml_seat) AS total_seat,
                            m.title as title,
                            ps.poster_name as poster_name
                        FROM
                            booking b
                        JOIN
                            schedule s USING(id_schedule)
                        JOIN
                            movies m USING(id_movie)
                        JOIN 
                            poster_image ps using(id_movie)
                        WHERE m.status='aktif'  AND YEARWEEK(tanggal_booking, 1) = YEARWEEK(CURDATE(), 1)
                        GROUP BY
                            m.id_movie
                    ) AS seat_summary;
                """)
    result = cur.fetchone()

    most_movie = {'jml_penonton' : result[0], 'title' : result[1], 'poster' : result[2]}

    return jsonify(most_movie)

# -----------------------------------------------------------------
# ----------------------- M I D T R A N S ------------------------- 
# -----------------------------------------------------------------

@app.route('/token-transaction', methods=['POST'])
def token_transaction() :
    try : 
        data = request.json 
        ticket = data['items']
        subtotal = data['subtotal']
        id_user = data['user_id']
        id_drink = data['id_drink']
        id_schedule = data['id_schedule']
        id_seat = data['id_seat']
        booking_id = generate_bookingId()
        qr_code = generate_qr(booking_id)

        items = []
        seat = []

        for x in ticket['id'] :
            price = ticket['price']/len(ticket['id'])-9000
            seat.append(x)
            items.append({"id" : x, 'price' : price, 'quantity' : 1, 'name' : 'Tiket Reguler'})


        cur = mysql.connection.cursor() 
        cur.execute("SELECT drink_name FROM drink WHERE id_drink=%s", (id_drink,))
        drink = cur.fetchone() 
        items.append({'id' : id_drink, 'price' : '9000', 'quantity' : len(ticket['id']), 'name' : drink[0]})

        cur.execute("SELECT nama, no_telp, alamat, email FROM users WHERE id_user=%s", (id_user,))
        user = cur.fetchone()

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qrcode', f'temp_qr_{booking_id}.png')
        send_file(f'temp_qr_{booking_id}.png',file_path, 'qrcode' )

        token = get_token(user, items, subtotal, booking_id, id_schedule, seat, qr_code, id_user, id_drink, id_seat)

        return jsonify(token), 200
    except Exception as e : 
        error_message = str(e)
        return jsonify({'Err' : True, 'message' : error_message}), 500

@app.route('/update-status-transaksi', methods=['POST'])
def status_transakasi() : 
    data = request.json
    status = data['status']
    id_booking = data['id_booking']

    if status == "settlement" : 
        status = 'success'

    cur = mysql.connection.cursor() 
    cur.execute("UPDATE booking SET status = %s WHERE id_booking = %s",(status, id_booking,))
    mysql.connection.commit() 

    return jsonify({'Err' : False, 'message' : 'Success Update Transaction Status!'}), 200



@app.route('/delete-booking-detail', methods=['POST'])
def delete_detail_booking() : 
    data = request.json
    id_booking = data['id_booking']

    cur = mysql.connection.cursor() 
    cur.execute("DELETE FROM detail_booking WHERE id_booking=%s",(id_booking,))
    mysql.connection.commit() 

    return jsonify({'Err' : False, 'message' : 'Success Update Transaction Status!'}), 200



@app.route('/notification_handler', methods=['POST'])
def notification_handler():
    print('Notification Handler')
    # request_json = request.get_json()
    request_json = request.json
    transaction_status_dict = core.transactions.notification(request_json)

    print(request_json)

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



# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------

def setPassword(password):
    password = bcrypt.generate_password_hash(password)
    return password



def checkPassword(hash, password):
    password = bcrypt.check_password_hash(hash, password)
    return password



# def generate_userId():
#     date = datetime.now().strftime('%m%d')
#     angka = ''.join(random.choices(string.digits, k=7))
#     user_id = f"{date}{angka}"



def generate_id_schedule(id_theaters):
    huruf = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"{id_theaters[:3]}{huruf}"



def get_price(id_theaters) : 
    days = datetime.now().strftime('%w')
    cur = mysql.connection.cursor()
    cur.execute("SELECT price1, price2, price3 FROM theaters WHERE id_theaters=%s",(id_theaters,))
    result = cur.fetchone()

    if days >='1' and days <='3' :
        return  int(result[0])
    elif days >= '4'  :
        return int(result[1])
    else :
        return int(result[2])



def format_tanggal(tanggal_string):
    tanggal = datetime.strptime(tanggal_string, '%a, %d %b %Y %H:%M:%S %Z')
    formatted_tanggal = tanggal.strftime('%d-%m-%Y')
    return formatted_tanggal


def generate_bookingId():
    angka = ''.join(random.choices(string.digits, k=5))
    id_booking = (f"{angka}") 
    return id_booking



def generate_user_id(birth_date):
    birth_year, birth_month, _ = birth_date.split('-')
    angka = ''.join(random.choices(string.digits, k=4))
    user_id = birth_month + birth_year + angka
    return user_id



def save_image(file, subfolder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
        file.save(file_path)
        send_file(filename, file_path, subfolder)



def send_file(name, file_path, subfolder):
    url = 'http://127.0.0.1:5000/save-image'
    
    with open(file_path, 'rb') as file:
        files = {'file': (name, file, 'multipart/form-data')}
        data = {'subfolder': subfolder}
        response = requests.post(url, files=files, data=data)

    return response.json()



def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def generate_movie_id():
    angka = ''.join(random.choices(string.digits, k=3))
    movie_id = f'MV{angka}'

    return movie_id



def update_pemabayaran(id_user): 
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = mysql.connection.cursor() 
    cur.execute("UPDATE booking SET status='cancel' WHERE id_user=%s AND status NOT IN ('success', 'pending') AND %s > batas_bayar", (id_user, date))



def format_datetime(date) :
    dateNow = datetime.now()
    dateBesok = dateNow + timedelta(days=1)

    if date == None :
        return dateBesok.strftime("%Y-%m-%d %H:%M:%S")

    db_date_obj = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
    formatted_date_str = db_date_obj.strftime("%d-%m-%Y %H:%M:%S")
    return(formatted_date_str)


# ---------------------------------------------------------------------------------
# -------------------- PENGGANTI TRIGGER MYSQL PYTHON ANYWHERE --------------------
# ---------------------------------------------------------------------------------

def update_tanggal_preorder(id_movie, new_preorder) :
    try :
        print('update_tanggal_preorder')
        cur = mysql.connection.cursor() 
        cur.execute("SELECT tanggal_rilis, preorder FROM movies WHERE id_movie=%s", (id_movie, ))
        result = cur.fetchone()
        old_preorder = result[1]
        tanggal_rilis = result[0]

        print(new_preorder)
        print(old_preorder)

        if new_preorder == 'ya' and old_preorder != 'ya' : 
            cur.execute("UPDATE movies SET tanggal_preorder= (%s - INTERVAL 7 DAY) WHERE id_movie=%s", (tanggal_rilis, id_movie))
            mysql.connection.commit() 
    except Exception as e :
        print(str(e))

def tanggal_preorder_on_rilis_change(id_movie, tanggal_rilis) :
    try :
        cur = mysql.connection.cursor() 
        cur.execute("UPDATE movies SET tanggal_preorder = %s + INTERVAL 7 DAY WHERE tanggal_rilis != %s AND id_movie = %s", (tanggal_rilis, tanggal_rilis, id_movie))
        mysql.connection.commit() 
        cur.close()
    except Exception as e :
        print(str(e))
    

@app.route('/get-test-payment', methods=['POST']) 
def test_get() :
    data = request.json 

    print(data)

    print(data['va_numbers'])
    print(data['va_numbers'][0]['va_number'])

    for x in data :
        print(x)
        

    return jsonify({'err' : False})



if __name__== "__main__":
    app.run(debug=True, port=4000)
