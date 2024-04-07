#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors
import secrets
import hashlib

from app import app
#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='root',
                       db='Roomio',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']


    cursor = conn.cursor()
    query = 'SELECT salt FROM users WHERE username = %s'
    cursor.execute(query, username)
    salt = cursor.fetchone()

    m = hashlib.sha256()
    m.update(password.encode())
    m.update(str(salt["salt"]).encode())
    password = m.hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM users WHERE username = %s and passwd = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        #return redirect(url_for('home'))
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    DOB = request.form['DOB']
    gender = request.form['gender']
    #convert gender into appropriate format for our database
    if(gender == "Male"):
        gender = 0
    else:
        gender = 1
    email = request.form['email']
    Phone = request.form['Phone']
    passwd = request.form['passwd']

    #create new salt

    salt = secrets.randbelow(10**16)

    m = hashlib.sha256()
    m.update(passwd.encode())
    m.update(str(salt).encode())
    passwd = m.hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM users WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO users VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, first_name, last_name, DOB, gender, email, Phone, passwd, salt))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    return render_template('home.html')

app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
#app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)