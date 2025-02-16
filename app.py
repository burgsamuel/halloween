from mailservice import email_confirmation_email, email_password_reset, email_multiple_login_attemps
from flask import Flask, render_template, request, flash, redirect, session, jsonify
from flask_limiter.util import get_remote_address
from datetime import timedelta, datetime
from requests.auth import HTTPBasicAuth
from bson.json_util import dumps
from flask_limiter import Limiter
from flask_session import Session
from flask_bcrypt import Bcrypt 
from mongo_db import HorseMongo
import requests
import threading
import random
import time




#### Halloween routes
import sqlFunctions


horses = HorseMongo()  # DB Instance



app = Flask(__name__)

app.config['SECRET_KEY'] = 're6723$^@#@(sdaKLNEKA@!###@_'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config["SESSION_TYPE"] = "filesystem"

bcrypt = Bcrypt(app) 
Session(app)           

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200000 per day"],
    storage_uri="memory://",
)



def email_verification_timeout(user):
    
    ''' Run a seperate thread to check if user verified their account in 10min
        If the user fails to varify their information will be deleted '''
    
    time_start = int(time.time())
    time_end = time_start + 600

    while True:
        if int(time.time()) >= time_end: # adding 10min 
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
        try:
            if session['regi']:
                count = 0
                if count > 3:
                    session.pop("regi", default=None)
                else:
                    count += 1
                    return render_template('register.html')
        except KeyError:
            pass
        
        if session['user']:

            print(f"Home Page: {session['user']} at: {datetime.now()}")

            user_data = horses.return_user_data(session['user'])

            user_last_on_wall = int(user_data['time_logged_wall_post'])
            resp = horses.check_wall_post_time()
            
            for i in resp:
                last_post_time = i['timeStored']
            new_posts = False    
            if user_last_on_wall < last_post_time:
                new_posts = True

            return render_template('home.html', homeActive=True, user=session['user'], new_posts=new_posts)
    except KeyError:
        return render_template('home.html', homeActive=True)



@app.get("/disclaimer")
def disclaimer():
    return render_template('disclaimer.html')




############################################
####    Paypal payment membership       ####
############################################

@app.get('/welcome')
def welcome_page():
    if session['user']:
        user_data = horses.return_user_data(session['user'])
        if user_data['verified'] and user_data['paid']:
            print(user_data)
            flash("The Punters House Society thanks you for your payment and wants to welcome you aboard!")
            return render_template('welcome.html', user=session['user'])
        else:
            return redirect('/register')
    else:
        return redirect('/')


@app.get("/membership_payment") 
def member_payment():
    if session['user']:
        user = session['user']
        amount = 10 # membership fees $AUD

        return render_template('payments/payment.html', amount=amount, user=user)
    else:
        return redirect("/register")
    

@app.post("/payments/<order_id>/capture")
def capture_payment(order_id):  # Checks and confirms payment
    captured_payment = approve_payment(order_id)

    if session['user'] is not None:

        if captured_payment['status'] == 'COMPLETED':
            time_paid = int(time.time())
            time_expire = time_paid + 31536002   # This is one year in seconds 
            horses.recieve_membership_payment(session['user'], time_paid, time_expire)

    # Redirect from within payment
    return jsonify(captured_payment)

def approve_payment(order_id):
    
    api_link = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
    client_id = "ASWtN-17xb16o1pIVYeMEIJDZJ3HuRvfpIznYS8Zr6lHEhAoCzN_B0jtWkxXpmpcjCwJqNdJPK9PR_Ms"
    secret = "ENJOGTvA4OvdVIABcwmK0b6f67UDyNgIub7mvyn_X1REstqmXiJ9KeNCY0XfOo6Wulcxq-tOu-PArN0B"
    basic_auth = HTTPBasicAuth(client_id, secret)
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(url=api_link, headers=headers, auth=basic_auth)
    response.raise_for_status()
    json_data = response.json()

    return json_data



############################################
####            Api Page                ####
############################################


@app.post('/api_data')
@limiter.limit("2000 per hour")
def api_data():
    
    '''
    API for collected horse data. Currently available to registered members.
    '''
    
    user = request.form['username']
    password = request.form['password']
    user_data = horses.return_user_data(user)
    

    if user_data is not None:
    
        hashed_password = user_data['hashed_password']        
        password_checked = bcrypt.check_password_hash(hashed_password, password)
        
        if password_checked:
            data = horses.retrive_mongo_data()
            json_data = dumps(data)
            return json_data
        else:
            return jsonify({"password": "Invalid"})            
    else:
        return jsonify({"User": "Invalid"})
    
    

############################################
####        Tips and Results Page       ####
############################################


@app.get('/tips')
def tips():  
    
    try:
        if session['user'] is not None:
            user = horses.check_user_exsists(session['user'])
            time_now = int(time.time())
            if user['verified']:
                if user['paid'] and (time_now <= user['paid_expire']):
                    user_last_on_wall = int(user['time_logged_wall_post'])
                    resp = horses.check_wall_post_time()
                    data = horses.retrive_mongo_data()
                    for i in resp:
                        last_post_time = i['timeStored']
                    new_posts = False    
                    if user_last_on_wall < last_post_time:
                        new_posts = True
                    return render_template('tips.html', tipsActive=True, data=data, timetest=time_now, timenow=time_now + 300, user=session['user'], new_posts=new_posts) 
                else:
                    flash("You have registered your email - Your Membership has not been paid!")
                    return redirect('/membership_payment')
            else:
                flash("Email not Verified!!")
                return redirect('/login')    
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
            user = horses.check_user_exsists(session['user'])
            if user['verified']:
                data = horses.retrive_mongo_result_data()
                return render_template('results.html', tipsActive=True, data=data, timenow=int(time.time() + 300), user=session['user']) 
            else:
                flash("Email not Verified!!")
                return redirect('/login')    
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
            data = horses.retrive_post_data(session['user'])
            return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)
    except KeyError:
        flash("Login to access this feature!")
        return render_template('home.html', homeActive=True)



@app.post('/submitPost')
@limiter.limit('100 per 1 hour')
def submit_post():
    try:
        if session['user'] is not None:          
            username = session['user']
            post_text = request.form['postText']
        horses.store_post_data(username, post_text)
        data = horses.retrive_post_data(session['user'])
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
        data = horses.retrive_post_data(session['user'])
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
        data = horses.retrive_post_data(session['user'])
        return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)
            
    except KeyError:
        flash("Something went wrong with the like button!")
        data = horses.retrive_post_data(session['user'])
        return render_template('wallPost.html', postsActive=True, user=session['user'], data=data)



############################################
####          login and Logout          ####
############################################

logins_attemps = {}
login_wait = {}

def login_try(user):
    if user in logins_attemps:
        counter = logins_attemps[user]
        counter += 1
        if counter <= 2:
            logins_attemps[user] = counter
            return False
        else:
            print(f"[WARNING] -- app.py login_try() -- {user} -- added to wait timer -- MULTIPLE ATTEMPS ****")
            if user in login_wait:
                pass
            else:
                login_wait[user] = int(time.time())
            return True
    else:
        logins_attemps[user] = 0
        return False
    

def login_wait_timer(user):

    timer_time = 600
    time_base = int(time.time())
    if user in login_wait:
        time_start = login_wait[user]
        test = time_base - time_start
        if test > timer_time:
            pass
        else:
            return True       
    else:
        return False


@app.get('/login')
def login_get():

    try:

        time_check = login_wait_timer(session["lots_of_logins"])

        if time_check:

            print(f"[WARNING] -- app.py -- login route -- {session["lots_of_logins"]} Still Attemping!")
            user_exsists = horses.check_user_exsists(session["lots_of_logins"])

            if user_exsists is not None:

                """ 
                    Send An email to a registered user if there has been multiple login attemps against their account
                """

                email_send = threading.Thread(target=email_multiple_login_attemps, args=(session["lots_of_logins"],))
                email_send.start()

                flash(f"Slow Down Phar Lap - Email has been sent to {session["lots_of_logins"]}")
                return render_template('home.html')
            
            else:

                print(f"[WARNING] -- app.py -- login -- POSSIBLE EMAIL GUESS")
                flash(f"Slow Down Phar Lap!!!!")
                return render_template('home.html')
            
        else:

            ''' Timer has expired for login attemps, so clear the user_name from the lists'''
            try:
                logins_attemps.pop(session["lots_of_logins"])
                login_wait.pop(session["lots_of_logins"])
                session.pop("lots_of_logins", default=None)
                return render_template('login.html', loginActive=True)

            except KeyError:

                return render_template('login.html', loginActive=True)
        
    except KeyError:

        return render_template('login.html', loginActive=True)    
    


@app.post("/login")
def login_post():

    if request.method == 'POST':

        user_name = request.form['email']
        password = request.form['password']
        time_check = login_wait_timer(user_name)

        if not time_check:

            if "@" not in user_name:

                user_exsists = None

            else:

                user_exsists = horses.check_user_exsists(user_name)

        else:

            print("[WARNING] -- app.py -- login post -- user activated login timer")
            flash(f"Slow Down Butter Cup")
            return render_template('home.html')

        if user_exsists is not None:
            
            hashed_password = user_exsists['hashed_password']
            password_checked = bcrypt.check_password_hash(hashed_password, password)
            
            if password_checked:

                try:
                    
                    if user_name in logins_attemps:
                        logins_attemps.pop(user_name)
                    if user_name in login_wait:
                        login_wait.pop(user_name)
                    session.pop("lots_of_logins", default=None)

                    session['user'] = request.form['email']
                    print("[SUCCESS] -- app.py -- login Post -- login attempts user data cleared! ")

                    return redirect('/tips')
                
                except KeyError:

                    session['user'] = request.form['email']
                    return redirect('/tips')
            
            else:

                result = login_try(user_name)
                if result:    

                    session["lots_of_logins"] = user_name      
                    flash(f"Slow Down Butter Cup")
                    return render_template('home.html')
                
                else:

                    print(f'[LOW] -- app.py -- login route -- {user_name} -- failed login!')
                    flash("Login details are not correct!")
                    return render_template('login.html', loginActive=True)
        else:

            print(f'[LOW] -- app.py -- login route -- {user_name} -- failed login!')
            flash("Username not valid!")
            return render_template('login.html', loginActive=True)
        
    else:

        try:

            time_check = login_wait_timer(session["lots_of_logins"])

            if time_check:

                print(f"[WARNING] -- app.py -- login route -- {session["lots_of_logins"]} Still Attemping!")
                user_exsists = horses.check_user_exsists(session["lots_of_logins"])

                if user_exsists is not None:

                    """ 
                        Send An email to a registered user if there has been multiple login attemps against their account
                    """

                    email_send = threading.Thread(target=email_multiple_login_attemps, args=(session["lots_of_logins"],))
                    email_send.start()

                    flash(f"Slow Down Phar Lap - Email has been sent to {session["lots_of_logins"]}")
                    return render_template('home.html')
                
                else:

                    print(f"[WARNING] -- app.py -- login -- POSSIBLE EMAIL GUESS")
                    flash(f"Slow Down Phar Lap!!!!")
                    return render_template('home.html')
                
            else:

                ''' Timer has expired for login attemps, so clear the user_name from the lists'''
                try:
                    logins_attemps.pop(session["lots_of_logins"])
                    login_wait.pop(session["lots_of_logins"])
                    session.pop("lots_of_logins", default=None)

                    return render_template('login.html', loginActive=True)
                
                except KeyError:
                    return render_template('login.html', loginActive=True)
            
        except KeyError:

            return render_template('login.html', loginActive=True)

        


@app.get('/logout')
def logout():
    session.clear()
    return redirect('/')




############################################
####           Registration             ####
############################################

@app.get('/register')
@limiter.limit("1000 per day")
def register():
    
    try:

        if session['user'] is not None:
            
            flash("You Have Registered Already!")
            return render_template('loginState.html', registerActive=True, user=session['user'])
        
        else:

            return render_template('form.html', registerActive=True) 
        
    except KeyError:

        return render_template('form.html', registerActive=True)


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
    session['regi'] = email
    
    email_confirmation_email(email, ver_code)
    clean_up_thread = threading.Thread(target=email_verification_timeout, args=(session['regi'],))
    clean_up_thread.daemon = True
    clean_up_thread.start()
    
    return render_template('register.html', user=firstname, email=email)




############################################
####           Reset Password           ####
############################################

     
@app.get('/passwordreset')
@limiter.limit("500 per day")
def password_reset():
    
    '''Password reset form. Just collects the users email'''
    
    return render_template('/password/form1.html')



@app.post('/passwordEmail')
@limiter.limit("300 per day")
def check_email():
    
    '''Returned from the form with users email to reset the password'''
    
    user_name = request.form['email']
    user_exsists = horses.check_user_exsists(user_name)
    
    if user_exsists is not None:
        
        ver_code = random.randint(10000, 99999)
        horses.ver_code_update(user_exsists['email'], ver_code)
        session['reset'] = user_exsists['email']
        print(ver_code)
        results = user_exsists['attemps']

        if int(results > 2):
            session.clear()
            flash("To many code attemps contact ADMIN!")
            return redirect('/')
        else:
            email = threading.Thread(target=email_password_reset, args=(user_exsists['email'], ver_code))
            email.start()

            return render_template('/password/checkcode.html', email=user_exsists['email'])       
    else:
        flash('Inncorect email address!')
        return render_template('/password/form1.html')
    
       
    
@app.post('/passwordCodeVerification')   
@limiter.limit("600 per day")
def check_code():
    
    user = session['reset']
    code = request.form['code']
    
    user_exsists = horses.check_user_exsists(user)
    stored_code = user_exsists['ver_code']
    
    if int(code) == int(stored_code):
        session['user'] = user

        return render_template('/password/newPassword.html')
    else:
        response, results = horses.attempt_counter(user)

        if int(results > 5):
            session.clear()
            return redirect('/')
        else:
            flash("Sorry that is an incorrect Code")
            return render_template('/password/checkcode.html')
   
    
@app.post('/submitNewPassword')
@limiter.limit("300 per day")
def update_new_password():
    
    '''Push new password to db'''
    
    new_password = request.form['password'] 
    
    if session['user'] is not None:
    
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        horses.update_password(session['user'], hashed_password)
        flash("Password has been updated 👍")
        return render_template('loginState.html')
        
    else:
        flash('Something Went Wrong!')
        return redirect('/')
    
    
    
############################################
####      Email Verification            ####
############################################    
    
    
@app.post('/emailVerification')
@limiter.limit("3500 per day")
def verify_email():
    user = session['regi']
    code = request.form['code']
    
    user_exsists = horses.check_user_exsists(user)
    stored_code = user_exsists['ver_code']

    
    if int(code) == int(stored_code):

        # User code successfully added
        session.pop('regi', default=None) # Clears the regi key after verification success

        session['user'] = user

        horses.update_verified(user)
        flash("Congratulations for Signing up to The Punters House Society")
        return redirect('/membership_payment')
    
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
    return render_template("/halloween/homepage.html")


@app.get("/location")
def add_location():
    return render_template("/halloween/addLocation.html")


@app.get("/mapView")
def map_view():
    return render_template("/halloween/mapview.html")


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
    app.run(debug=True, host='0.0.0.0')
