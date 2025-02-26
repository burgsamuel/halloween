from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from dotenv import load_dotenv
import time
import os


class HorseMongo():
    
    def __init__(self):
    
        load_dotenv()
        self.password = os.getenv('MONGOPASSWORD')
        self.url = f'mongodb+srv://admin:{self.password}@cluster0.r2jvy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
    
    
    
    ############################################################
    ##########               Tips Data               ###########
    ############################################################
    
    
    def retrive_mongo_data(self):
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        horses = database.get_collection('todays_races')
        
        response = horses.find().sort({'raceTime': 1})
        
        return response
        



    def retrive_mongo_result_data(self):
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        horses = database.get_collection('todays_races')
        
        response = horses.find().sort({'raceTime': -1})
        
        return response
    


    ############################################################
    ##########            User Registration          ###########
    ############################################################    
    

    def register_user(self, first, last,  email, hashed_pass, mobile, street_address, mailing_address, state, post_code, ver_code, verified, attemps):
        
        '''Inserts User Information into MongoDB Altas'''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        user.insert_one({
            'first_name' : first,
            'last_name'  : last,
            'email' : email,
            'hashed_password' : hashed_pass,
            'mobile_number' : mobile,
            'street_address' : street_address, 
            'mailing_address' : mailing_address, 
            'state' : state, 
            'post_code' : post_code,
            'ver_code' : ver_code,
            'verified' : verified,
            'attemps' : attemps,
            'time_logged': 0,
            'time_logged_wall_post': int(time.time())
        })
        
        return user
    
    

    def update_Users(self):
        
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')

        user.update_many( {} , { '$set': { 'time_logged_wall_post': 10 } })

    
    def log_user(self, email):
        ''' Log the timer on user database, going to be used to check for new posts etc '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        query = {'email' : email}
        update = { '$set' : { 'time_logged' : int(time.time())} }
        
        user.update_one(query, update)
        
        return
    
    
    
    
    def check_user_exsists(self, email):
        
        ''' Checks to See if the email address has been registered already '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        query = {'email' : email}
        update = { '$set' : { 'time_logged' : int(time.time())} }
        
        user.update_one(query, update)

        # Check if User has been registered already
        response = user.find_one({'email': email})
        
        return response
    
    
    
    def return_user_data(self, email):
        
        ''' Checks to See if the email address has been registered already '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')

        response = user.find_one({'email': email})
        
        return response
    
    

    def update_verified(self, email):
        
        ''' Checks to See if the email address has been verified and updates it '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        query_filter = {'email': email}
        update_operation = {'$set': { 'verified' : True }}
        
        response = user.update_one(query_filter, update_operation)
        
        return response


    def attempt_counter(self, email):
        
        ''' add failed attempts to attempt counter to track user attempts '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        # Check if User has been registered already
        user_name = user.find_one({"email": email})
        attemps = int(user_name['attemps']) + 1


        query_filter = {'email': email}
        update_operation = {'$set': { 'attemps' : attemps }}
        
        response = user.update_one(query_filter, update_operation)
        
        return response, attemps
    
    
    def delete_user_registration(self, email):
        
        ''' If failed the registration too many times remove their data '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        user_name = user.find_one({"email": email})
        is_verified = user_name['verified']
        
        if is_verified:
            return is_verified
        else:
            query_filter = {'email': email}
            response = user.delete_one(query_filter)
            print('Unverified User removed')
            return response
        



    ############################################################
    ##########            Password  Reset            ###########
    ############################################################
    
    
    def ver_code_update(self, email, code):
        
        ''' add failed attempts to attempt counter to track user attempts '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')

        query_filter = {'email': email}
        update_operation = {'$set': { 'ver_code' : code }}
        
        response = user.update_one(query_filter, update_operation)
        
        return response    



    def update_password(self, email, hashed_password):
        
        ''' Checks to see if user is their than updates password '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        query_filter = {'email': email}
        update_operation = {'$set': { 'hashed_password' : hashed_password }}
        
        response = user.update_one(query_filter, update_operation)
        
        return response

    
        
    ############################################################
    ##########            User Post Data             ###########
    ############################################################
    
        
    def store_post_data(self, user, post):
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        horses = database.get_collection('posts')
        
        time_stored = int(time.time()) 
        
        formated_time = time.strftime('%c', time.localtime(time_stored + 39600))
            
        if formated_time[0] == '0' or formated_time[0] == 0:
            formated_time = formated_time[1:]
            
            formated_time = formated_time
        
        
        horses.insert_one({
            'user' : user,
            'timeStored' : time_stored,
            'format_time': formated_time,
            'post' : post,
            'likes': 0,
        })
        
        return horses
    
    
    
    def retrive_post_data(self, email):
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        horses = database.get_collection('posts')
        
        response = horses.find().sort({'timeStored': -1})
        
        
        #Update user timer when they last visited post page        
        user = database.get_collection('Users')
        query = {'email' : email}
        update = { '$set' : { 'time_logged_wall_post' : int(time.time())} }
        
        user.update_one(query, update)
        
        
        return response
    
    
    def check_wall_post_time(self):
        
        
        '''Retrive the last post and time to make notifications for user'''
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        horses = database.get_collection('posts')
        
        response = horses.find().sort({'timeStored': -1}).limit(1)
        
        return response



    def delete_post_data(self, post_id):
        
        ''' Check for an id on a post than delete it from mongoDB  '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('posts') 

        query_filter = {"_id": ObjectId(post_id)}
        response = user.delete_one(query_filter)
        
        return response
    
    
    def add_post_like(self, post_id):
        
        ''' Checks to See if the email address has been verified and updates it '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('posts')
        
        collection = user.find_one({"_id": ObjectId(post_id)})
        likes = int(collection['likes']) + 1
        
        query_filter = {"_id": ObjectId(post_id)}
        update_operation = {'$set': { 'likes' : likes }}
        
        response = user.update_one(query_filter, update_operation)
        
        
        return response

              

