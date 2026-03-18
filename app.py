from flask import Flask, render_template, request, flash, redirect, session, jsonify, send_from_directory
from mailservice import email_confirmation_email, email_password_reset
from flask_limiter.util import get_remote_address
from bson.json_util import dumps
from flask_limiter import Limiter
from flask_session import Session
from flask_bcrypt import Bcrypt 
from mongo_db import HorseMongo
from datetime import timedelta
from datetime import datetime
import threading
import random
import time
import os

from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler
import json



horses = HorseMongo()  # DB Instance



app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=10)
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

@app.get('/healthz')
def health_check():
    return "OK", 200


@app.get("/")
def home():
    try:
        if session['user']:
            user_data = horses.return_user_data(session['user'])
            user_last_on_wall = int(user_data['time_logged_wall_post'])
            resp = horses.check_wall_post_time()

            for i in resp:
                last_post_time = i['timeStored']
                new_posts = False
                if user_last_on_wall < last_post_time:
                    new_posts = True

                # ✅ ADD THIS (fast file read, no DB)
                home_stats = read_home_stats()

                return render_template(
                    "home.html",
                    homeActive=True,
                    user=session['user'],
                    new_posts=new_posts,
                    home_stats=home_stats  # ✅ pass into template
                )
    except KeyError:
        # ✅ Also pass it for logged-out users (optional but nice)
        home_stats = read_home_stats()
        return render_template("home.html", homeActive=True, home_stats=home_stats)
    
    
    
# @app.get("/") 
# def home():
#     try: 
#         if session['user']:
#             user_data = horses.return_user_data(session['user'])
#             user_last_on_wall = int(user_data['time_logged_wall_post'])
#             resp = horses.check_wall_post_time()
#             for i in resp:
#                 last_post_time = i['timeStored']
#             new_posts = False    
#             if user_last_on_wall < last_post_time:
#                 new_posts = True
                
#         return render_template('home.html', homeActive=True, user=session['user'], new_posts=new_posts)
#     except KeyError:
#         return render_template('home.html', homeActive=True)


@app.get("/disclaimer")
def disclaimer():
    return render_template('disclaimer.html')



@app.post('/api_data')
@limiter.limit("2000 per hour")
def api_data():
    
    
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
   


def group_by_track(raw_data):
    tracks = defaultdict(lambda: {"horses": []})

    for entry in raw_data:
        race_name = entry.get("race")
        if not race_name:
            continue

        # Extract track name (everything before " Race")
        track = race_name.split(" Race")[0]

        # Horse name
        horse = entry.get("horse") or entry.get("raceDetails", {}).get("horseName")

        # Position
        pos = entry.get("finishPosition", "").strip()
        if not pos.isdigit():
            continue
        pos = int(pos)

        # Jockey
        jockey = (
            entry.get("jockeyName")
            or entry.get("raceDetails", {}).get("jockeyName")
            or "Unknown"
        )
        if isinstance(jockey, str) and jockey.startswith("J: "):
            jockey = jockey.replace("J: ", "").strip()

        # Trainer
        trainer = (
            entry.get("trainerName")
            or entry.get("raceDetails", {}).get("trainerName")
            or "Unknown"
        )
        if isinstance(trainer, str) and trainer.startswith("T: "):
            trainer = trainer.replace("T: ", "").strip()

        # Silk image
        silk = entry.get("bibLink")
        if silk:
            if silk.startswith("//"):
                silk = "https:" + silk
        else:
            silk = None

        # Date from timestamp
        ts = entry.get("timeStored")
        if ts:
            date_str = datetime.fromtimestamp(ts).strftime("%d %b %Y")
        else:
            date_str = "Unknown"

        tracks[track]["horses"].append({
            "horse": horse,
            "position": pos,
            "date": date_str,
            "timestamp": ts or 0,
            "jockey": jockey,
            "trainer": trainer,
            "silk": silk,
            "openPrice": entry.get("raceDetails", {}).get("openPrice"),
            "placePrice": entry.get("raceDetails", {}).get("placePrice")

        })

    # Sort horses: 1st → 2nd → 3rd → etc, newest first within each position
    for track in tracks.values():
        track["horses"].sort(key=lambda x: (x["position"], -x["timestamp"]))

    return tracks




def read_home_stats():
    """Loads precomputed home stats from static/home_stats.json (fast, no DB)."""
    path = os.path.join("static", "home_stats.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------
# PRE‑RENDER FUNCTION — RUNS DAILY OR ON FIRST VISIT
# ---------------------------------------------------
def build_past_results_page():
    with app.app_context():
        print("Building pre-rendered past results page...")
        raw_data = horses.retrive_mongo_past_results()
        grouped = group_by_track(raw_data)
        html = render_template(
            "pastraces.html",
            pastResults=True,
            tracks=grouped,
            timenow=int(time.time()),
            user="SYSTEM"
        )

        output_path = os.path.join("static", "past_results.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print("Past results page generated.")




# ---------------------------------------------------
# HOME STATS PRE-COMPUTE — RUNS DAILY (QUIET HOURS)
# ---------------------------------------------------
def build_home_stats():
    with app.app_context():
        print("Building home stats...")

        raw_data = horses.retrive_mongo_past_results()  # same dataset you already use for past results [1](https://onedrive.live.com?cid=79ED6D1B2ED618AD&id=79ED6D1B2ED618AD!s1082c610a4e5460b9af0d9ffb5f58307)
        now_ts = int(time.time())

        seven_days_ago = now_ts - (7 * 86400)
        thirty_days_ago = now_ts - (30 * 86400)

        # Helper to safely parse positions
        def parse_pos(entry):
            pos = (entry.get("finishPosition") or "").strip()
            return int(pos) if pos.isdigit() else None

        # Helper to extract track name like your group_by_track() does [1](https://onedrive.live.com?cid=79ED6D1B2ED618AD&id=79ED6D1B2ED618AD!s1082c610a4e5460b9af0d9ffb5f58307)
        def get_track(entry):
            race_name = entry.get("race") or ""
            if " Race" in race_name:
                return race_name.split(" Race")[0]
            return race_name or "Unknown"

        # Filter windows
        last7 = []
        last30 = []
        for e in raw_data:
            ts = e.get("timeStored") or 0
            if ts >= seven_days_ago:
                last7.append(e)
            if ts >= thirty_days_ago:
                last30.append(e)

        # Last 7 days stats
        total7 = 0
        wins7 = 0
        places7 = 0
        recent_winners = []  # small list for mobile

        for e in last7:
            pos = parse_pos(e)
            if pos is None:
                continue
            total7 += 1
            if pos == 1:
                wins7 += 1
                recent_winners.append({
                    "horse": e.get("horse") or e.get("raceDetails", {}).get("horseName") or "Unknown",
                    "track": get_track(e),
                    "ts": e.get("timeStored") or 0
                })
            if pos in (1, 2, 3):
                places7 += 1

        win_sr_7d = round((wins7 / total7) * 100, 1) if total7 else 0.0
        place_sr_7d = round((places7 / total7) * 100, 1) if total7 else 0.0

        # Sort winners newest-first and limit to keep it mobile-friendly
        recent_winners.sort(key=lambda x: x["ts"], reverse=True)
        recent_winners = recent_winners[:3]

        # Days since last win (overall, not just 7d)
        last_win_ts = None
        for e in raw_data:
            pos = parse_pos(e)
            ts = e.get("timeStored") or 0
            if pos == 1:
                if last_win_ts is None or ts > last_win_ts:
                    last_win_ts = ts

        if last_win_ts:
            days_since_last_win = int((now_ts - last_win_ts) / 86400)
        else:
            days_since_last_win = None

        # Top track performance (last 30d): pick track with most wins
        track_counts = {}  # track -> {wins, total}
        for e in last30:
            pos = parse_pos(e)
            if pos is None:
                continue
            track = get_track(e)
            track_counts.setdefault(track, {"wins": 0, "total": 0})
            track_counts[track]["total"] += 1
            if pos == 1:
                track_counts[track]["wins"] += 1

        top_track = None
        if track_counts:
            top_track = max(track_counts.items(), key=lambda kv: kv[1]["wins"])[0]
            top_track_wins = track_counts[top_track]["wins"]
            top_track_total = track_counts[top_track]["total"]
            top_track_sr = round((top_track_wins / top_track_total) * 100, 1) if top_track_total else 0.0
        else:
            top_track_wins = top_track_total = top_track_sr = 0

        stats = {
            "generated_at_ts": now_ts,
            "last7": {
                "total": total7,
                "wins": wins7,
                "places": places7,
                "win_sr": win_sr_7d,
                "place_sr": place_sr_7d,
                "recent_winners": recent_winners
            },
            "top_track_30d": {
                "track": top_track,
                "wins": top_track_wins,
                "total": top_track_total,
                "win_sr": top_track_sr
            }
        }

        out_path = os.path.join("static", "home_stats.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False)

        print("Home stats generated.")



# -----------------------------
# DAILY SCHEDULER (3 AM)
# -----------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(build_past_results_page, "cron", hour=3, minute=0)
scheduler.add_job(build_home_stats, "cron", hour=3, minute=5)
scheduler.start()



# -----------------------------
# Warm cache on startup (once)
# -----------------------------

# Past results page
past_results_path = os.path.join("static", "past_results.html")

if not os.path.exists(past_results_path):
    build_past_results_page()


# Home stats
home_stats_path = os.path.join("static", "home_stats.json")

if not os.path.exists(home_stats_path):
    build_home_stats()



# ---------------------------------------------------
# NEW ENDPOINT — SERVES PRE‑RENDERED STATIC HTML
# ---------------------------------------------------
@app.get('/pastresults')
@limiter.limit("8000 per hour")
def past_results():

    # Must be logged in
    if session.get('user') is None:
        flash("Please Login/Register!")
        return redirect('/login')

    # Must be verified
    user = horses.check_user_exsists(session['user'])
    if not user['verified']:
        flash("Email not Verified!!")
        return redirect('/login')

    # Path to pre-rendered file
    file_path = os.path.join("static", "past_results.html")

    # If file missing (first run), build it once
    if not os.path.exists(file_path):
        build_past_results_page()

    # Serve instantly
    return send_from_directory("static", "past_results.html")

    

# @app.get('/pastresults')
# @limiter.limit("8000 per hour")
# def past_results():
#     try:
#         if session.get('user') is not None:
#             user = horses.check_user_exsists(session['user'])

#             if user['verified']:

#                 raw_data = horses.retrive_mongo_past_results()

#                 # NEW grouping
#                 grouped = group_by_track(raw_data)

#                 return render_template(
#                     'pastraces.html',
#                     pastResults=True,
#                     tracks=grouped,
#                     timenow=int(time.time()),
#                     user=session['user']
#                 )

#             else:
#                 flash("Email not Verified!!")
#                 return redirect('/login')

#         else:
#             flash("Please Login/Register! ")
#             return redirect('/login')

#     except KeyError:
#         flash("Please Login/Register! ")
#         return redirect('/login')
   
    

    
############################################
####        Tips and Results Page       ####
############################################


@app.get('/tips')
def tips():  
    
    try:
        if session['user'] is not None:
            user = horses.check_user_exsists(session['user'])
            if user['verified']:
                user_last_on_wall = int(user['time_logged_wall_post'])
                resp = horses.check_wall_post_time()
                data = horses.retrive_mongo_data()
                for i in resp:
                    last_post_time = i['timeStored']
                new_posts = False    
                if user_last_on_wall < last_post_time:
                    new_posts = True
                return render_template('tips.html', tipsActive=True, data=data, timetest=int(time.time()), timenow=int(time.time()), user=session['user'], new_posts=new_posts) 
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
                return render_template('results.html', tipsActive=True, data=data, timenow=int(time.time()), user=session['user'])  
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

     
   
 
     
if __name__ == "__main__":
    app.run()