from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os


class HorseMongo():
    
    def __init__(self):
    
        load_dotenv()
        self.password = os.getenv('MONGOPASSWORD')
        self.url = f'mongodb+srv://admin:{self.password}@cluster0.r2jvy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
    
    
    
    
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
            'attemps' : attemps
        })
        
        return user
    
    
    def check_user_exsists(self, email):
        
        ''' Checks to See if the email address has been registered already '''
        
        # Create a new client and connect to the server
        client = MongoClient(self.url, server_api=ServerApi('1'))

        database = client.get_database('horse_data')
        user = database.get_collection('Users')
        
        # Check if User has been registered already
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