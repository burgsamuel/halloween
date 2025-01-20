from flask import Flask, render_template, request, flash, redirect, session, jsonify
from mailservice import email_confirmation_email
from flask_session import Session
from flask_bcrypt import Bcrypt 
from mongo_db import HorseMongo
from datetime import timedelta
import threading
import random
import time

#### Halloween routes
import sqlFunctions


horses = HorseMongo()  # DB Instance



app = Flask(__name__)
app.config['SECRET_KEY'] = 're6723$^@#@(sdaKLNEKA@!###@_'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config["SESSION_TYPE"] = "filesystem"

bcrypt = Bcrypt(app) 
Session(app)           
          

def email_verification_timeout(user):
    
    ''' Run a seperate thread to check if user verified their account in 10min
        If the user fails to varify their information will be deleted '''
    
    time_start = time.time()
    time_end = time_start + 600

    while True:
        if time.time() >= time_end: # adding 10min 
            horses.delete_user_registration(user) # Function checks verification before deleting
            return
        else:
            time.sleep(30)


############################################
####            Home Page               ####
############################################

@app.get("/") 
def home():
    try: 
        if session['user']:
            pass
        return render_template('home.html', homeActive=True, user=session['user'])
    except KeyError:
        return render_template('home.html', homeActive=True)



############################################
####        Tips and Results Page       ####
############################################

@app.get('/tips')
def tips():  
    
    try:
        if session['user'] is not None:
            # user = horses.check_user_exsists(session['user'])
            # if user['verified']:
            data = horses.retrive_mongo_data()
            return render_template('tips.html', tipsActive=True, data=data, timenow=(time.time() + 300), user=session['user']) 
            # else:
                # flash("Email not Verified!!")
                # return redirect('/login')    
        else:
            flash("Please Login/Register! ")
            return redirect('/login')
    except KeyError:
        flash("Please Login/Register! ")
        return redirect('/login')
    

@app.get('/results')
def results():
    try:
        if session['user'] is not None:
            # user = horses.check_user_exsists(session['user'])
            # if user['verified']:
                data = horses.retrive_mongo_result_data()
                return render_template('results.html', tipsActive=True, data=data, timenow=(time.time() + 300), user=session['user']) 
            # else:
            #     flash("Email not Verified!!")
            #     return redirect('/login')    
        else:
            flash("Please Login/Register! ")
            return redirect('/login')
    except KeyError:
        flash("Please Login/Register! ")
        return redirect('/login')



############################################
####            Post/Forum             ####
############################################


@app.get('/wallPost')
def get_wall():
    try: 
        if session['user'] is not None:
            data = horses.retrive_post_data()
            return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)
    except KeyError:
        flash("Login to access this feature!")
        return render_template('home.html', homeActive=True)


@app.post('/submitPost')
def submit_post():
    try:
        if session['user'] is not None:          
            username = session['user']
            post_text = request.form['postText']
        horses.store_post_data(username, post_text)
        data = horses.retrive_post_data()
        return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)
            
    except KeyError:
        flash("Something went wrong with post!")
        return render_template('wallPost.html', postsActive=True, user=session['user'])
    
    
@app.post('/removePost')
def remove_post():
    try:
        if session['user'] is not None:          
            post_id = request.form['id_of_post']
            horses.delete_post_data(post_id)
        data = horses.retrive_post_data()
        return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)
            
    except KeyError:
        flash("Something went wrong with post!")
        return render_template('wallPost.html', postsActive=True, user=session['user'])
    

@app.post('/addlike')
def add_likes():
    try:
        if session['user'] is not None:       
            post_id = request.form['like-button']
            horses.add_post_like(post_id)
        data = horses.retrive_post_data()
        return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)
            
    except KeyError:
        flash("Something went wrong with the like button!")
        data = horses.retrive_post_data()
        return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)



############################################
####          login and Logout          ####
############################################

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_name = request.form['email']
        password = request.form['password']
        user_exsists = horses.check_user_exsists(user_name)

        if user_exsists is not None:
            
            hashed_password = user_exsists['hashed_password']
            
            password_checked = bcrypt.check_password_hash(hashed_password, password)
            
            if password_checked:
                session['user'] = request.form['email']
                return redirect('/tips')
            else:
                flash("Login details are not correct!")
                return render_template('login.html', loginActive=True)
        else:
            flash("Username not valid!")
            return render_template('login.html', loginActive=True)
    return render_template('login.html', loginActive=True)


@app.get('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.get('/register')
def register():
    

    try:
        if session['user'] is not None:
            
            flash("You Have Registered Already!")
            return render_template('loginState.html', registerActive=True, user=session['user'])
        else:
            return render_template('form.html', registerActive=True) 
    except KeyError:
        return render_template('form.html', registerActive=True)




############################################
####           Registration             ####
############################################

@app.post('/register')
def register_post():
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    password = request.form['password']
    mobile_number = request.form['mobile']
    street_address = request.form['address']
    mail_address = request.form['mailingaddress']
    state = request.form['state']
    post_code = request.form['postcode']
    
    ver_code = random.randint(1000, 9999)
    verified = False
    attemps = 0
    #check if email already exsists
    data = horses.check_user_exsists(email)
    
    if data is not None:
        flash('This Email has already been registered!')
        return render_template('form.html')
    
    else:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    
    horses.register_user(firstname, lastname, email, hashed_password, mobile_number, street_address, mail_address, state, post_code, ver_code, verified, attemps)
    session['user'] = email
    
    email_confirmation_email(email, ver_code)
    clean_up_thread = threading.Thread(target=email_verification_timeout, args=(session['user'],))
    clean_up_thread.daemon = True
    clean_up_thread.start()
    
    return render_template('register.html', user=firstname, email=email)

     
    
    
    
############################################
####      Email Verification            ####
############################################    
    
@app.post('/emailVerification')
def verify_email():
    user = session['user']
    code = request.form['code']
    
    user_exsists = horses.check_user_exsists(user)
    stored_code = user_exsists['ver_code']

    
    if int(code) == int(stored_code):
        session['user'] = user
        response = horses.update_verified(user)

        flash("You have successfully been verified")
        return redirect('/tips')
    else:
        response, results = horses.attempt_counter(user)

        if int(results > 2):
            horses.delete_user_registration(user)
            session.clear()
            flash("Too many Wrong attemps!")
            return redirect('/logout')
        else:
            flash("Sorry that is an incorrect Code")
            return render_template('register.html')

     
     
     
#######################################################
#####           Halloween APP                   #######
#######################################################     
  
@app.get("/spotter")
def home_page():
    return render_template("homepage.html")


@app.get("/location")
def add_location():
    return render_template("addLocation.html")


@app.get("/mapView")
def map_view():
    return render_template("mapview.html")


@app.get("/mapData")
def collect_map_data():
    data = sqlFunctions.retrieve_data()
    return jsonify(data)


@app.post("/locationData")
def recieve_location():
    data = request.get_json()
    sqlFunctions.save_data(data)
    return {"Status": "Recieved location and Saved ✅"}


@app.post("/RemoveUserSpots")
def remove_spots():
    data = request.get_json()
    res = sqlFunctions.remove_spots(data['id'])
    return {"TotalSpots": res,
            "Success": "Spots Removed"}   
     
   
 
     
if __name__ == "__main__":
    app.run()