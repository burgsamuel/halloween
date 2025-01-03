from flask import Flask, render_template, request, jsonify
import sqlFunctions


app = Flask(__name__)


@app.get("/")
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