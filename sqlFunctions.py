import sqlitecloud
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv('API_KEY')


url = f'sqlitecloud://cfx4laonhk.sqlite.cloud:8860/halloweenSpots?apikey={API_KEY}'

def connect_sql():
    conn = sqlitecloud.connect(url)
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS users (
            userid INTEGER,
            latitude REAL,
            longitude REAL,
            timestamp INTEGER,
            iconurl TEXT
        )""")  # noqa: F841

    conn.commit()
    c.close()
    
    
    
def save_data(data):
    
    conn = sqlitecloud.connect(url)
    c = conn.cursor()
    
    c.execute("""INSERT INTO users VALUES(
                :userid, :latitude, :longitude, :timestamp, :iconurl)""",
                {'userid': data['id'], 'latitude': data['lat'], 'longitude': data['lon'],
                 'timestamp': data['time_stamp'], 'iconurl': data['iconUrl']})
    
    conn.commit()
    c.close()
    
    
    
def retrieve_data():
    
    conn = sqlitecloud.connect(url)
    c = conn.cursor()
    
    c.execute("""SELECT * FROM users""")
    data = c.fetchall()
    
    conn.commit()
    c.close()
    
    retrieved_data = []
    
    for d in data:
        data_info = {}
        data_info['userid']     = d[0]
        data_info['latitude']   = d[1]
        data_info['longitude']  = d[2]
        data_info['timestamp']  = d[3]
        data_info['iconurl']    = d[4]
        
        retrieved_data.append(data_info)
    
    return retrieved_data
    

def remove_spots(user_id):
    
    conn = sqlitecloud.connect(url)
    c = conn.cursor()
    
    c.execute("DELETE FROM users WHERE userid = :id", {'id': user_id})
    
    conn.commit()
    c.close()
    
    return {"Delete" : True}