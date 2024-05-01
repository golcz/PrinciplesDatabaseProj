#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors
import secrets
import hashlib

#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'some key that you will never guess'

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
    if('username' in session):
        return redirect(url_for('home'))
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    if('username' in session):
        return redirect(url_for('home'))
    return render_template('login.html')

#Define route for home
@app.route('/home')
def home():
    if(not('username' in session)):
        return redirect(url_for('hello'))
    return render_template('home.html', username = session['username'])


#Define route for register
@app.route('/register')
def register():
    if('username' in session):
        return redirect(url_for('home'))
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():

    if('username' in session):
        return redirect(url_for('home'))

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
        return render_template('home.html', username = session['username'])
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():

    if('username' in session):
        return redirect(url_for('home'))


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
        cursor.close()
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO users VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, first_name, last_name, DOB, gender, email, Phone, passwd, salt))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/logout')
def logout():
    if(not('username' in session)):
        return redirect(url_for('home'))
    session.pop('username')
    return redirect('/')

@app.route('/searchBuilding')
def searchBuilding():
    if(not('username' in session)):
        return redirect(url_for('home'))
    return render_template('searchBuilding.html')

@app.route('/searchBuildingForm',  methods=['GET', 'POST'])
def searchBuildingForm():

    if(not('username' in session)):
        return redirect(url_for('home'))

    building = request.form['building']
    company = request.form['company']
    
    cursor = conn.cursor();
    query = 'SELECT unitRentID, unitNumber, monthlyRent, squareFootage, availableDateForMoveIn \
    FROM Apartmentunit WHERE companyName = %s AND buildingName = %s'
    cursor.execute(query, (company, building))
    data = cursor.fetchall()

    if(not(data)):
        error = "No such building!"
        render_template('searchUnits.html', error = error)


    query = 'SELECT aType FROM Provides WHERE companyName = %s AND buildingName = %s'
    cursor.execute(query, (company, building))
    amen = cursor.fetchall()

    query = 'SELECT COUNT(unitRentID) AS count \
    FROM Apartmentunit WHERE companyName = %s AND buildingName = %s'
    cursor.execute(query, (company, building))
    numUnit = cursor.fetchone()

    query = 'SELECT petName, isAllowed, registrationFee, monthlyFee FROM Pets NATURAL JOIN Petpolicy WHERE companyName = %s AND buildingName = %s\
    AND username = %s'
    cursor.execute(query, (company, building, session["username"]))
    pets = cursor.fetchall()

    query = 'SELECT buildingName, companyName, addrNum, addrStreet, addrCity, addrState, addrZipCode, yearBuilt \
    FROM ApartmentBuilding WHERE companyName = %s AND buildingName = %s'
    cursor.execute(query, (company, building))
    build = cursor.fetchone()

    cursor.close()
    return render_template('showBuilding.html', amen = amen, numUnit = numUnit, build = build, units=data, pets=pets)

@app.route('/searchUnit', methods=['GET', 'POST'])
def searchUnit():

    if(not('username' in session)):
        return redirect(url_for('home'))

    city = request.form['city']
    unitID = request.form['unit']

    cursor = conn.cursor();
    query = 'SELECT unitRentID, companyName, buildingName, unitNumber, monthlyRent, squareFootage, availableDateForMoveIn \
    FROM Apartmentunit WHERE unitRentID = %s'
    cursor.execute(query, unitID)
    data = cursor.fetchone()

    query = 'SELECT COUNT(name) as count FROM Rooms WHERE unitRentID = %s'
    cursor.execute(query, unitID)
    rooms = cursor.fetchone()

    query = 'SELECT username, roommateCnt, moveInDate FROM Interests WHERE unitRentID = %s'
    cursor.execute(query, unitID)
    interest = cursor.fetchall()

    query = 'SELECT username, rating, comment FROM Comments WHERE unitRentId = %s'
    cursor.execute(query, unitID)
    comments = cursor.fetchall()

    query = 'SELECT AVG(monthlyRent) as num FROM Apartmentunit NATURAL JOIN ApartmentBuilding WHERE squareFootage/1.1<%s AND squareFootage/0.9>%s AND addrCIty = %s'
    cursor.execute(query,(data['squareFootage'],data['squareFootage'],city))
    avg = cursor.fetchone()

    cursor.close()
    return render_template('showUnit.html', unit = data, rooms = rooms, interest = interest, comments = comments, avg = avg )


@app.route('/postInterest', methods=['GET', 'POST'])
def postInterest():

    if(not('username' in session)):
        return redirect(url_for('home'))

    count = request.form['count']
    date = request.form['date']
    unit = request.form['unit']

    cursor = conn.cursor();
    query = 'INSERT INTO interests VALUES(%s, %s, %s, %s)'
    cursor.execute(query, (session["username"], unit, count, date))
    conn.commit()
    cursor.close()

    return render_template('home.html', username = session['username'])


@app.route('/postComment', methods=['GET', 'POST'])
def postComment():

    if(not('username' in session)):
        return redirect(url_for('home'))

    rating = request.form['rating']
    comment = request.form['comment']
    unit = request.form['unit']

    cursor = conn.cursor();
    query = 'INSERT INTO Comments VALUES(%s, %s, %s, %s, %s)'
    cursor.execute(query, (None, unit, session["username"], rating, comment))
    conn.commit()
    cursor.close()

    return render_template('home.html', username = session['username'])


@app.route('/pet')
def pet():

    if(not('username' in session)):
        return redirect(url_for('home'))

    cursor = conn.cursor();
    query = 'SELECT petName, petType, petSize FROM Pets WHERE username = %s'
    cursor.execute(query, session["username"])
    data = cursor.fetchall()
    cursor.close()

    return render_template('pet.html', pets = data)


@app.route('/petAdd')
def petAdd():

    if(not('username' in session)):
        return redirect(url_for('home'))

    return render_template('petAdd.html')

@app.route('/petAddForm', methods=['GET', 'POST'])
def petAddForm():

    if(not('username' in session)):
        return redirect(url_for('home'))

    petName = request.form['petName']
    petType = request.form['petType']
    petSize = request.form['petSize']

    cursor = conn.cursor();
    query = 'SELECT * FROM Pets WHERE petName = %s AND petType = %s AND username = %s'
    cursor.execute(query, (petName, petType, session["username"]))
    data = cursor.fetchone()

    error = None
    if(data):
        error = "You already have a pet with this name and type"
        cursor.close()
        return render_template('petAdd.html', error = error)
    else:
        query = 'INSERT INTO Pets VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (petName, petType, petSize, session["username"]))
        conn.commit()

        cursor.close()
        return render_template('home.html', username = session['username'])


@app.route('/petModify')
def petModify():

    if(not('username' in session)):
        return redirect(url_for('home'))

    return render_template('petModify.html')

@app.route('/petModifyForm', methods=['GET', 'POST'])
def petSelectForm():


    if(not('username' in session)):
        return redirect(url_for('home'))

    oldPetName = request.form['oldPetName']
    oldPetType = request.form['oldPetType']

    newPetName = request.form['newPetName']
    newPetType = request.form['newPetType']
    newPetSize = request.form['newPetSize']


    cursor = conn.cursor();
    query = 'SELECT * FROM Pets WHERE petName = %s AND petType = %s AND username = %s'
    cursor.execute(query, (oldPetName, oldPetType, session["username"]))
    data = cursor.fetchone()

    if(not(data)):
        error = "Pet not found"
        cursor.close()
        return render_template('petModify.html', error = error)
    
    if(oldPetName != newPetName or oldPetType != newPetType):
        cursor = conn.cursor();
        query = 'SELECT * FROM Pets WHERE petName = %s AND petType = %s AND username = %s'
        cursor.execute(query, (newPetName, newPetType, session["username"]))
        data = cursor.fetchone()
        if(data):
            error = "Another pet with the newly speicfied name and type already exists"
            cursor.close()
            return render_template('petModify.html', error = error)


    cursor = conn.cursor();
    query = 'UPDATE Pets SET petName = %s, petType = %s, petSize = %s WHERE petName = %s AND petType = %s AND username = %s'
    cursor.execute(query, (newPetName, newPetType, newPetSize, oldPetName, oldPetType, session["username"]))
    conn.commit()
    cursor.close()

    return render_template('home.html', username = session['username'])
        
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)