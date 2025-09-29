from quart import Quart, render_template, request, jsonify, flash, session, redirect

import mailservice
import threading
import mongodb
import time
import os


try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    print("dotenv not found!")



app = Quart(__name__)

app.secret_key = os.getenv("SECRETKEY")
app.config["SESSION_TYPE"] = "filesystem"

login_attemps = []

@app.get('/')
async def home_page():
    try:
        if session["verification_pending"]:
            return await render_template("login/emailVerify.html")
    except KeyError:
        pass
    try:
        if session["logged_in"]:
            return await render_template("homepage.html", user=session["logged_in"])
    except KeyError:
        return await render_template("homepage.html")


@app.get("/logout")
async def logout():
    session.clear()
    await flash("Logged Out Successfully.")
    return await render_template("homepage.html")
    
    
@app.get("/location")
async def add_location():
    return await render_template("addLocation.html")


@app.get("/userspots")
async def update_user_spots():
    try:
        if session["logged_in"]:
            userspots = mongodb.retrieve_user_spots(session["logged_in"])
            return ({"spots" : userspots})
    except KeyError:
        return ( { "spots" : "Fail" } )


@app.get("/mapView")
async def map_view():
    return await render_template("mapview.html")


@app.get("/mapData")
async def collect_map_data():
    data = mongodb.retrieve_data()
    return jsonify(data)


@app.post("/locationData")
# Store a new Spot after checking login and timer
async def recieve_location():
    try:
        if session["logged_in"]:
            user_data = mongodb.check_user_exsists(session["logged_in"])
            try:
                total_spots = user_data['total_spots']
                last_spot_time = user_data["time_last_spot"]
                time_now = time.time()
                if time_now >= last_spot_time + 60 and total_spots <= 100:
                    data = await request.get_json()
                    mongodb.store_mongo_data(data, session["logged_in"])
                    increament_user_spots = threading.Thread(target=mongodb.update_user_spots, args=(session["logged_in"],))
                    increament_user_spots.start()
                    return {"Status": "Recieved location and Saved ✅"}
                else:
                    return { "TimeLeft": ((last_spot_time + 60) - time_now), "TimeWait" : True } 
            except KeyError:
                print('Error with key in adding location data')
                return {"KeyError": True}                
    except KeyError:
        return {"Failed": True}
    
    
@app.post("/RemoveUserSpots")
async def remove_spots():
    try:
        if session["logged_in"]:
            # data = await request.get_json()
            # print(data)
            res = mongodb.remove_users_spots(session['logged_in'])
            return {"TotalSpots": res,
                "Success": "Spots Removed from data base"}
    except KeyError:
        return {"TotalSpots": 0,
                "Fail": "Login or Register!"}
    
    
########################################################
## Login End Points
########################################################


@app.get("/loginForm")
async def login_form():
    
    try:
        if session["logged_in"]:
            await flash("You are already logged in 🎃")
            return await render_template("homepage.html", user=session["logged_in"])
    except KeyError:
        pass
        
    try:
        ip_address = request.remote_addr
    except Exception as error:
        print(error)
        ip_address = "Address Unavailable"
    login_data = {
        "ip" : ip_address,
        "attemps" : 0,
        "end_time" : 0
    }
    
    for index, item in enumerate(login_attemps):
        if item["ip"] == ip_address:
            if item["attemps"] >= 3:
                time_now = time.time()
                if time_now >= item["end_time"]:
                    login_attemps.pop(index)
                    
                    return await render_template("login/loginForm.html")
                else:
                    time_left = (int(item["end_time"]) - int(time_now)) / 60
                    flash(f"Please wait: {round(time_left)}-mins before trying again!!")
                    return await render_template("infopage.html", bad=True)
    
    for items in login_attemps:
        if ip_address == items["ip"]:
            return await render_template("login/loginForm.html")
    login_attemps.append(login_data)

    return await render_template("login/loginForm.html")

    
@app.post("/login")
async def login_request():
    
    username = (await request.form)["username"]
    password = (await request.form)["password"]
    try:
        ip_address = request.remote_addr
    except Exception as error:
        print(error)
        ip_address = "Address Unavailable"
    

    for item in login_attemps:
        if item["ip"] == ip_address:
            if item["attemps"] >= 3:
                # set a timer to restrict user access 
                item["end_time"] = time.time() + 1200

                await flash("Too many failed attempts!!!")
                return await render_template("infopage.html", bad=True)
    
    if len(password) <= 7:
        for item in login_attemps:
            if item["ip"] == ip_address:
                item["attemps"] += 1
        await flash("Incorrect Password!")
        return await render_template("login/loginForm.html") 
    
    user_data = mongodb.check_user_exsists(username)
    
    if user_data is not None:
        hashed_password = user_data["password"]
        result = mongodb.check_user_login(hashed_password, password) #check hashed password
    else:
        await flash("User Details Not Found!")
        return await render_template("login/loginForm.html")    
    if result:
        
        session["logged_in"] = username
        for index, item in enumerate(login_attemps):
            if item["ip"] == ip_address:
                login_attemps.pop(index)
        return await render_template("homepage.html", user=username)
    else:
        for item in login_attemps:
            if item["ip"] == ip_address:
                item["attemps"] += 1
        print(*login_attemps)
        await flash("Incorrect Password!")
        return await render_template("login/loginForm.html")    



#  Delete User From DB
@app.post("/removeAccount")
async def delete_account():
    
    password = await request.get_json()

    try:
        if session["logged_in"]:
            user_data = mongodb.check_user_exsists(session["logged_in"])
        if user_data is not None:
            hashed_password = user_data["password"]
            result = mongodb.check_user_login(hashed_password, password['password']) #check hashed password
        else:
            await flash("User Details Not Found!")
            return await render_template("homepage.html", user=session['logged_in'])
        
        if result:
            # Delete user from DB
            mongodb.remove_users_spots(session['logged_in']) # Delete Spots
            mongodb.delete_user_from_db(session['logged_in'])# Delete User
            session.clear()
            
            
            return {"AccountDeleted" : True }
            
        else:
            return {"AccountDeleted" : False}    
    except KeyError:
        return {"AccountDeleted" : False}
    
    return {"AccountDeleted" : False } 



def start_timer():
    start = time.time()
    end = start + 20
    print("start timer")
    while True:
        if time.time() >= end:
            print("End time")
            return True
        else:
            time.sleep(5)



########################################################
## Registration
########################################################

@app.get("/registrationForm")
async def registration_form():
    return await render_template("login/register.html")


@app.post("/registration")
async def registration_post():
    
    form_data = await request.form
    
    # username = (await request.form)["username"]
    # email = (await request.form)["email"]
    # password = (await request.form)["password"]  
    # bot_field = (await request.form)["email-field"]
    username = form_data['username']
    email = form_data['email']
    password = form_data['password']
    bot_field = form_data.get('email-field')
    
    if bot_field and len(bot_field) > 0:
        print("honey pot triggered")
        await flash("Registration Successful, Thank you")
        return await render_template("homepage.html")       
    
    
    # Check if User already exsists
    user = mongodb.check_user_exsists(username)
    email_exsists = mongodb.check_user_email(email)
    if user is not None:
        await flash("Username Already Taken!")
        return await render_template("login/register.html")
    if email_exsists is not None:
        await flash("Email Already Registered!")
        return await render_template("login/register.html")
    else:
        verification_code = mongodb.create_user(username, email, password)
        # print(f"Verification Code: {verification_code}")
        mail_thread = threading.Thread(target=mailservice.email_confirmation, args=(email, verification_code))
        mail_thread.start()
        session["verification_pending"] = username
        verification_code_timer = threading.Thread(target=mongodb.verification_timer, args=(username,))
        verification_code_timer.start()
        return await render_template("login/emailVerify.html", email=email, user=username)


@app.post("/verificationcode")
async def verify_user_email():
    
    username = session["verification_pending"]
    form = await request.form
    code = int(form["code"])
    
    user_data = mongodb.check_user_exsists(username)
    
    try:
        user_attemps = user_data["verification_attempts"]
    except:  # noqa: E722
        session.clear()
        await flash("Time to verifiy has passed!")
        return await render_template("homepage.html", bad=True)
    
    if username is not None and user_attemps < 4:
        
        emailed_code = int(user_data["verification_code"])
        # print(f"Emailed Code: {emailed_code}")
        
        if emailed_code == code:
            
            session.pop("verification_pending", default=None)
            session["logged_in"] = user_data["username"]
            verify_email = threading.Thread(target=mongodb.email_verified, args=(username,))
            verify_email.start()
            await flash("Code Verified!")
            return await render_template("homepage.html", user=session["logged_in"])
        
        else:
            mongodb.email_verify_attempts(username)
            await flash("Incorrect code!")
            return await render_template("login/emailVerify.html")
    else:
        
        session.clear()
        await flash("You Have Entered Code Wrong Too Many Times!!")
        return await render_template("homepage.html", bad=True)


########################################################
## Password Reset
########################################################

@app.get("/resetpassword")
async def reset_password():
    return await render_template("passwordreset/resetform.html")



@app.post("/passwordresetemail")
async def reset_password_post():
    username = (await request.form)["username"]
    email = (await request.form)["email"]
    
    user_data = mongodb.check_user_exsists(username)
    
    if user_data is not None:
        saved_email = user_data["email"]
        if email != saved_email:
            await flash("Sorry incorrect details!")
            return await render_template("infopage.html", bad=True)
        else:
            # Set new verification code in DB
            verification_code = mongodb.password_reset_verification_code(username)
            send_email = threading.Thread(target=mailservice.email_password_reset, args=(saved_email, verification_code))
            send_email.start()
            # print(verification_code)
            session["email_reset"] = username
            return await render_template("passwordreset/passwordresetcode.html", user=username, email=saved_email)
    
    return await render_template("passwordreset/resetform.html")


@app.post("/passwordresetcode")
async def verify_password_code():

    user_code = (await request.form)["code"]
    try:
        username = session["email_reset"]
    except KeyError:
        return redirect("/")

    user_data = mongodb.check_user_exsists(username)
    
    try:
        user_attemps = user_data["verification_attempts"]
        end_time = user_data["end_timer"]
    except Exception as error:
        print(error)
        session.clear()
        await flash("Error in password reset!")
        return await render_template("infopage.html", bad=True)
    
    if username is not None and user_attemps < 4 and time.time() < end_time:
        
        emailed_code = int(user_data["verification_code"])
        # print(f"Emailed Code: {emailed_code}")
    
        if int(emailed_code) == int(user_code):
            
            reset_counters = threading.Thread(target=mongodb.password_code_verified, args=(username,))
            reset_counters.start()    
            # New Password
            await flash("Code Verified!")
            return await render_template("passwordreset/newpassword.html")
            
        else:
                   
            mongodb.email_verify_attempts(username)
            await flash("Incorrect code!")
            return await render_template("passwordreset/passwordresetcode.html")
    else:
        
        session.clear()
        if time.time() > end_time:
            await flash("Reset has timed out!!")
        else:
            await flash("You Have Entered Code Wrong Too Many Times!!")
        return await render_template("homepage.html", bad=True)


@app.post("/updatepassword")
async def store_new_password():
    
    try:
        username = session["email_reset"]
    except Exception as error:
        print(error)
        return await redirect("/")

    unhased_password = (await request.form)["password"]
    
    
    store_new_password = threading.Thread(target=mongodb.update_new_password, args=(username, unhased_password))
    store_new_password.start()
    session.clear()
    session["logged_in"] = username
    await flash("Password Reset and logged in!")
    return await render_template("homepage.html", user=session["logged_in"])
    
    
    

########################################################
## Start app
########################################################




if __name__ == '__main__':
    app.run()