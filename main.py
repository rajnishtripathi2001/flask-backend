# import libraries
from flask import Flask, jsonify, render_template, request
import os, time
from dotenv import load_dotenv
from pymongo import MongoClient
from flask_cors import CORS
from flask_mail import Mail, Message

# load environment variables
load_dotenv()

# Access the environment variables for the email
mail_username = os.environ.get('MAIL_USERNAME')
mail_password = os.environ.get('MAIL_PASSWORD')

# initialize flask app
app = Flask(__name__, template_folder='templates')

# Configure the flask app
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = mail_username
app.config['MAIL_PASSWORD'] = mail_password
app.config['MAIL_DEFAULT_SENDER'] = mail_username

# Initialize the mail extension
mail = Mail(app)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# connect to mongodb
cluster = MongoClient(os.getenv("MONGO_URL"))
db = cluster["test"]


"""------------------- API Routes -------------------"""

# Home route
@app.route('/')
def index():
    # rendeing home.html template
    return render_template('home.html')

# Login API route
@app.route(os.getenv("LOGIN_ROUTE"), methods=['POST'])
def login():
    request_data = request.json
    # get data from mongodb
    collection = db["admins"]
    try:
        result = collection.find_one(
            {"userID": request_data["username"], "passwd": request_data["password"]})
        if result:
            return jsonify({"message": "Successful", "login": True, "ID": result["_id"]})
        else:
            return jsonify({"message": "Failed"})
    except Exception as e:
        return jsonify({"error": str(e)})

#  Create a new admin API route
@app.route(os.getenv("CREATE_ADMIN"), methods=['POST'])
def create_admin():
    # insert into mongodb
    collection = db["admins"]
    try:
        username = request.json["userID"]
        password = request.json["passwd"]
        id = int(time.time()*1000)

        result = {"userID": username, "passwd": password, "_id": id}
        collection.insert_one(result)
        return jsonify({"message": "New Admin created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})

# Send email API route
@app.route(os.getenv("SEND_EMAIL"), methods=['POST'])
def send_email():
    subject = request.json["subject"]
    recipient = request.json["to"]
    body = request.json["message"]

    if not (subject and recipient and body):
        return jsonify({"message": "Missing data!"})

    msg = Message(subject=subject, sender=mail_username,
                  recipients=[recipient])
    msg.body = body
    mail.send(msg)

    return jsonify({"message": "Successful"})

# Find User API route
@app.route(os.getenv("Find_USER"), methods=['POST'])
def find_user():
    request_data = request.json
    # get data from mongodb
    collection = db["users"]
    try:
        result = collection.find_one({"_id": request_data["id"]})
        if result:
            return jsonify({"message": "Successful", "user": True, "Info": result})
        else:
            return jsonify({"message": "Failed"})
    except Exception as e:
        return jsonify({"error": str(e)})

# update User API route
@app.route(os.getenv("UPDATE_USER"), methods=['POST'])
def update_user():
    request_data = request.json
    collection = db["users"]
    try:
        update = {
            "fname": request_data["temData"]['fname'],
            "lname": request_data["temData"]['lname'],
            "email": request_data["temData"]['email'],
            "password": request_data["temData"]['password'],
        }
        collection.find_one_and_update(
            {"_id": request_data["id"]}, {"$set": update})
        return jsonify({"message": "Successfully updated"})
    except Exception as e:
        return jsonify({"error : ", str(e)})

# Restric User API route
@app.route(os.getenv("RESTRICT_USER"), methods=['POST'])
def restrict_user():
    request_data = request.json
    collection = db["users"]
    try:
        collection.find_one_and_update({"_id": request_data["id"]},{"$set": {"status": "Restricted"}})
        print(request_data)
        return jsonify({"message": "Successfully Restricted"})
    except Exception as e:
        return jsonify({"error": str(e)})

# Remove Restriction from the  Restriced User API route
@app.route(os.getenv("REMOVE_RESTRICTION"), methods=['POST'])
def unrestrict_user():
    request_data = request.json
    collection = db["users"]
    try:
        collection.find_one_and_update({"_id": request_data["id"]},{"$set": {"status": "Active"}})
        print(request_data)
        return jsonify({"message": "Successfully Restriction Removed"})
    except Exception as e:
        return jsonify({"error": str(e)})

# Delete User API route
@app.route(os.getenv("DELETE_USER"), methods=['POST'])
def delete_user():
    request_data = request.json
    collection = db["users"]
    collection2 = db["wallets"]
    try:
        collection.find_one_and_delete({"_id": request_data["id"]})
        collection2.find_one_and_delete({"_id": request_data["id"]})
        return jsonify({"message": "Successfully Deleted"})
    except Exception as e:
        return jsonify({"error": str(e)})



if __name__ == '__main__':
    app.run(debug=True,port=os.getenv("PORT", default=5000))
