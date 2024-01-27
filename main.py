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
@app.route(os.getenv("FIND_USER"), methods=['POST'])
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

# Get all Orders listed API route
@app.route(os.getenv("ORDERS"), methods=['GET'])
def orders():
    collection = db["orders"]
    try:
        result = collection.find().sort('createdAt', -1)
        if result:
            return jsonify({"message": "Successful", "orders": True, "Info":list(result)})
        else:
            return jsonify({"message": "Failed"})
    except Exception as e:
        return jsonify({"error": str(e)})
    
# Mark Order as Delivered and send mail API route
@app.route(os.getenv("DELIVERED"), methods=['POST'])
def delivered():
    request_data = request.json
    collection = db["orders"]
    collection2 = db["users"]
    try:
        collection.find_one_and_update({"_id": request_data["id"]},{"$set": {"action": "Done"}})
        email = collection2.find_one({"_id": request_data["uID"]})
        
        subject = "Order Delivered"
        recipient = email["email"]
        body = "Your order has been delivered successfully."
        if not (subject and recipient and body):
          return jsonify({"message": "Missing data!"})
        msg = Message(subject=subject, sender=mail_username,recipients=[recipient])
        msg.body = body
        mail.send(msg)

        return jsonify({"message": "Successfully Delivered"})
    except Exception as e:
        return jsonify({"error": str(e)})
    
# Get all Transactions listed API route
@app.route(os.getenv("TRANSACTIONS"),methods=['GET'])
def transactions():
    collection = db["transactions"]
    try:
        result = collection.find().sort('createdAt', -1)
        if result:
            return jsonify({"message": "Successful", "orders": True, "Info":list(result)})
        else:
            return jsonify({"message": "Failed"})
    except Exception as e:
        return jsonify({"error": str(e)})

# Verify the Transaction
@app.route(os.getenv("VERIFY_TRANSACTION"),methods=['POST'])
def verify_transaction():
    request_data = request.json
    collection = db['transactions']

    try:
        collection.find_one_and_update({"_id": request_data["id"]},{"$set": {"verification": "Verified"}})
        return jsonify({"message": "Successfully Verified the transaction"})

    except Exception as e:
        return jsonify({"error": str(e)})

# Find Wallet API route
@app.route(os.getenv("FIND_WALLET"),methods=['POST'])
def find_wallet():
    request_data = request.json
    collection = db["wallets"]

    try:
        result  = collection.find_one({"_id":request_data["walletID"]})
        if(result ):
            return jsonify({"message":"Found","result":result})
        else:
            return jsonify({"message":"Not Found"})

    except Exception as e:
        return jsonify({"error": str(e)})

# Update Wallet API route
@app.route(os.getenv("UPDATE_WALLET"),methods=['POST'])
def update_wallet():
    request_data = request.json
    collection = db["wallets"]

    try:
        if(request_data["list"]["task"] == "addMoney"):
            collection.find_one_and_update({"_id": request_data["list"]["id"]},{"$set": {"balance": request_data["list"]["amount"]}})
            return jsonify({"message": "Successfully Updated the wallet"})

    except Exception as e:
        return jsonify({"error": str(e)})

# Get User's All transaction
@app.route(os.getenv("ALL_TRANSACTIONS"),methods=["POST"])
def get_transactions():
    request_data = request.json
    collection = db["transactions"]

    try:
        result = collection.find({"uID":request_data["walletID"]}).sort('createdAt', -1)
        if result:
            return jsonify({"message": "Transaction Found", "result":list(result)})
        else:
            return jsonify({"Message":"No Transaction Found"})



    except Exception as e:
        return jsonify({"Error":str(e)})

# Wallet State Management API route
@app.route(os.getenv("WALLET_STATE"),methods=["POST"])
def wallet_state():
    request_data = request.json
    collection = db["wallets"]
    
    collection.find_one_and_update({"_id":request_data["task"]["id"]},{"$set": {"walletstatus": request_data["task"]["state"]}})

    return jsonify({"message":"Action Completed"})


if __name__ == '__main__':
    app.run(debug=True,port=os.getenv("PORT", default=5000))
