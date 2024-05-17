import midtransclient
import random
import string
from main import app, mysql
import json
import os
from datetime import datetime



# Create Snap API instance
snap = midtransclient.Snap(
    # Set to true if you want Production Environment (accept real transaction).
    is_production=False,
    server_key= 'SB-Mid-server-MkWPtSUBmoSSOJ4UkdcyilCC'
)
def get_token(userData, items, subtotal, booking_id, id_schedule, seat, qr_code, id_user, id_drink, id_seat) : 
    # Build API parameter
    date = datetime.now().strftime('%Y-%m-%d')
    jml_seat = len(seat)
    try : 
        cur = mysql.connection.cursor() 
        cur.execute("""INSERT INTO booking (id_booking, id_user, id_schedule, id_drink, tanggal_booking, jml_seat, total, qrcode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (booking_id, id_user, id_schedule, id_drink, date, jml_seat, subtotal, qr_code))

        for no_seat, seat_id in list(zip(seat, id_seat)) :
                cur.execute("INSERT INTO detail_booking (id_booking, no_seat, id_seat) VALUES (%s, %s, %s)", (booking_id, no_seat, seat_id))

        mysql.connection.commit()
        cur.close()
    except Exception as e :
        print(e)
    



    param = {
        "transaction_details": {
            "order_id": booking_id,
            "gross_amount": subtotal
        }, "credit_card":{
            "secure" : True
        }, "item_details": items, 
        "billing_address" : {
            "first_name" : userData[0],
            "address" : userData[2],
            "phone" : userData[1],
            "country_code" : "IDN",
        },
        "shipping_address" : {
            "first_name" : userData[0],
            "address" : userData[2],
            "phone" : userData[1],
            "country_code" : "IDN",
        },
        "customer_details":{
            "first_name": userData[0],
            "email": userData[3],
            "phone": userData[1],
            "billing_address": {
                "first_name" : userData[0],
                "address" : userData[2],
                "phone" : userData[1],
                "country_code" : "IDN",
            },
            "shipping_address": {
                "first_name" : userData[0],
                "address" : userData[2],
                "phone" : userData[1],
                "country_code" : "IDN",
            }
        }
    }

    transaction = snap.create_transaction(param)

    transaction_token = transaction['token']

    
    return transaction_token


