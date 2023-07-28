from flask import *
from twilio.rest import *
import random
import hashlib
from flask_sqlalchemy import SQLAlchemy;
from flask_login import UserMixin
app= Flask(__name__)
import sqlite3 as sqlite
import socket
import base64
import requests
import face_recognition
import io
import numpy as np
import secrets
from datetime import datetime
import pytz

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
app.config['SECRET_KEY']= 'amongussus'
db=SQLAlchemy(app)
app.secret_key = 'amongussus'
hostname=socket.gethostname()
#hostip=socket.gethostbyname(hostname)
hostip="192.168.0.103"

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/otp')
def otp():
    return render_template('otp.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

def getOTP(number,user):
    #number= request.form['number']
    #return number
    token = generate_token()
    
    val,tid= getOTPApi(number,user,token)
    d={
        'token':tid
    }
    if val:
        return render_template('enterOTP.html',data=d)
    #could be changed to send to function which would thus render the template
def generate_token():
    return secrets.token_hex(16)

def generateOTP():
    return random.randrange(10000,99999)

def getOTPApi(number,username,token):
    account_sid = 'AC78eecd157484992ef11db08707966a9d'
    auth_token = '5b70233fe04cbce13cc7e7ee7e43937b'
    client= Client(account_sid, auth_token)
    otp = generateOTP()
    

    connection=sqlite.connect("database.db")
    cursor=connection.cursor()
    query="INSERT INTO tokens (token, username) VALUES('"+token+"','"+username+"')" #here token id can be random for now its auto
    cursor.execute(query)
    connection.commit()
    #can create a token log table to make note of the actual tokens used for login

    query="SELECT id from tokens where token= '"+token+"'"
    cursor.execute(query)
    result=cursor.fetchone()
    tid=result[0]
     #here token id can be random for now its auto
    cursor.execute("INSERT INTO tokenlog (tokenid, token) VALUES(?,?)",(tid,token))
    connection.commit()

    connection.close()

    body = 'Your OTP is '+ str(otp)+' and Go to this url to verify your face: https://'+hostip+':5000/upload_photo/'+token
    message = client.messages.create(
        from_='+15156047432',
        body=body,
        to=number
    )
    otp = hashlib.sha256(str(otp).encode('utf-8')).hexdigest()
    session['response']=str(otp)
    if message.sid:
        return True,tid
    else: return False,tid

@app.route("/verify_face", methods=["POST"])
def verify_face():
  token = request.form["token"]

  image = request.form["captured_image"]
  photo= image
  image =image.split(",")[1]
  image = base64.b64decode(image)
  image = io.BytesIO(image)
  image = face_recognition.load_image_file(image)
  face_encodings = face_recognition.face_encodings(image)

  connection=sqlite.connect("database.db")
  cursor=connection.cursor()
  
  query="SELECT username from tokens where token='"+token+"'"
  cursor.execute(query)
  result=cursor.fetchone()
  username=result[0]

  query="SELECT face_data from users where username='"+username+"'"
  cursor.execute(query)
  result=cursor.fetchone()
  connection.close()

  encoding_bytes=result[0]
  act_encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
  #act_encoding = np.reshape(act_encoding, (1, 128))
  face_locations = face_recognition.face_locations(image)
  num_faces = len(face_locations)
  if(num_faces>1):
    return "Error: multiple faces found... Retry again"
  matches = face_recognition.compare_faces(act_encoding, face_encodings, tolerance=0.5)
  if matches[0]== True:
    connection=sqlite.connect("database.db")
    cursor=connection.cursor()
    query="DELETE FROM tokens WHERE token ='"+token+"'"
    cursor.execute(query)
    current_datetime = datetime.now(pytz.timezone("Asia/Kolkata"))
    cursor.execute("INSERT INTO logs (face_data ,username,token,login_time) VALUES(?,?,?,?)",(photo,username,token,current_datetime))
    connection.commit()
    connection.close()
    return "Face detected and verified. You can move on!!!!!"
  else:
    return "Invalid user face please restart the login process."


@app.route('/upload_photo/<token>', methods=['GET', 'POST'])
def upload_photo(token):
        d={
            'user':"",
            'hereFor':'verify_face',
            'token':token
        }
        return render_template('upload_photo.html',data=d)

@app.route('/validateOTP',methods=['POST'])
def validateOTP():
    otp =request.form['otp']
    tid =request.form['token']
    if 'response' in session:
        s = session['response']
        session.pop('response',None)

        connection=sqlite.connect("database.db")
        cursor=connection.cursor()
        query="SELECT token from tokenlog where tokenid='"+tid+"' "
        cursor.execute(query)
        result=cursor.fetchone()
        token=result[0]
        query="SELECT * from tokens where token='"+token+"' "
        cursor.execute(query)
        result=cursor.fetchone()
        connection.close()
        if hashlib.sha256(str(otp).encode('utf-8')).hexdigest()!=s or result:
            return render_template('not_authorised.html')
        else:
            connection=sqlite.connect("database.db")
            cursor=connection.cursor()
            query="SELECT username,face_data,login_time from logs where token='"+token+"' "
            cursor.execute(query)
            result=cursor.fetchone()
            connection.close()
            d={
        'user':result[0],
        'photo':result[1],
        'logtime':result[2]
        } 
        return render_template('authorised.html',data=d)
        
@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    connection=sqlite.connect("database.db")
    cursor=connection.cursor()
    username =request.form['username']
    password =request.form['password']
    hashlib.sha256(str(password).encode('utf-8')).hexdigest()
    cursor.execute("SELECT username,password,mobile_number from users where username=? and password=?",(username,password))
    result=cursor.fetchone()
    connection.close()
    if(result):
        number=result[2]
        return getOTP(number,username)
    else: return "Invalid Login"

@app.route('/insertFace',methods=['POST'])
def insertFace():
    connection=sqlite.connect("database.db")
    cursor=connection.cursor()
    image = request.form["captured_image"].split(",")[1]
    user = request.form["user"]
    image = base64.b64decode(image)
    image = io.BytesIO(image)
    image = face_recognition.load_image_file(image)
    face_encodings = face_recognition.face_encodings(image)
    face_locations = face_recognition.face_locations(image)
    num_faces = len(face_locations)
    if(num_faces>1):
        connection=sqlite.connect("database.db")
        cursor=connection.cursor()
        query="DELETE FROM users WHERE username ='"+user+"'"
        cursor.execute(query)
        connection.commit()
        connection.close()
        return "Error: multiple faces found"
    encoding_bytes = np.array(face_encodings).tobytes()
    result=cursor.execute("UPDATE users SET face_data = ?  WHERE username = ?",(encoding_bytes,user))
    connection.commit()
    connection.close()
    return f"done {user} :) {result}"

@app.route('/validateReg',methods=['POST'])
def validateReg():
    connection=sqlite.connect("database.db")
    cursor=connection.cursor()
    username =request.form['username']
    password =request.form['password']
    mobile =request.form['mobile']
    hashlib.sha256(str(password).encode('utf-8')).hexdigest()
    query="INSERT INTO users (username, password, mobile_number) VALUES('"+username+"','"+password+"','"+mobile+"')"
    cursor.execute(query)
    connection.commit()
    connection.close()
    d={
        'user':username,
        'hereFor':'insertFace',
        'token':""
    }
    return render_template('upload_photo.html',data=d)


if __name__ =='__main__':
    app.config['SESSION_TYPE'] = 'otp'
    app.run(host=hostip,debug =False, ssl_context=('server.crt', 'server.key'))
    #app.run(host=hostip,debug =True)