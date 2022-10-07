from flask import Flask
from flask_restful import Api
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.BankApi
users = db["Users"]


def user_exist(username):
    if users.count_documents({"Username": username}) == 0:
        return False
    else:
        return True


def verify_password(username, password):
    if not user_exist(username):
        return False
    hashed_password = users.find({"Username": username})[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_password) == hashed_password:
        return True
    else:
        return False


def get_cash(username):
    cash = users.find({"Username": username})[0]["Own"]
    return cash


def find_user_debt(username):
    debt = users.find({"Username": username})[0]["Debt"]
    return debt


def generate_return_dictionary(status, message):
    retJson = {"status": status, "message": message}
    return retJson


# returns a tuple of Error => first is message and the second is True/False
def verify_credentials(username, password):
    if not user_exist(username):
        return generate_return_dictionary(301, "invalid username"), True

    correct_password = verify_password(username, password)
    if not correct_password:
        return generate_return_dictionary(302, "invalid password"), True

    # means no error
    return None, False


def update_account(username, balance):
    users.update({"Username": username}, {"$set": {"Own": balance}})


def update_debt(username, balance):
    users.update({"Username": username}, {"$set": {"Debt": balance}})

