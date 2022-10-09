from flask import Flask, request, jsonify
from flask_restful import Api, Resource

from utils import user_exist, verify_credentials, generate_return_dictionary, get_cash, update_account, find_user_debt,\
    update_debt, users
import bcrypt

app = Flask(__name__)
api = Api(app)


class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        if user_exist(username):
            retJson = {"status": 301, "message": "invalid username or user already exists"}
            return jsonify(retJson)

        hashed_pass = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        users.insert_one({"Username": username, "Password": hashed_pass, "Own": 0.0, "Debt": 0.0})

        retJson = {"username": username, "Own": 0.0, "Debt": 0.0, "message": "you have successfully registered"}
        return jsonify(retJson)


class Add(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)
        if money <= 0:
            return jsonify(generate_return_dictionary(304, "invalid amount deposited"))

        cash = get_cash(username)

        # Bank charges
        money -= 1
        # update bank's account
        bank_cash = get_cash("BANK")
        update_account("BANK", bank_cash + 1)

        # update user balance
        current_balance = cash + money
        update_account(username, current_balance)

        # should have returned this but preferred the beneath one
        retJn = generate_return_dictionary(200, "deposit successful")

        return jsonify({"status": 200, "username": username, "balance": current_balance})


class Transfer(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        transfer_to = postedData["to"]
        money = postedData["amount"]

        # verify credentials
        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        # verify balance
        cash = get_cash(username)
        if cash <= 0:
            return jsonify(generate_return_dictionary(304, "insufficient balance, add or take a loan"))

        # what is the recipient does not exist
        if not user_exist(transfer_to):
            return jsonify(generate_return_dictionary(301, "Receiver does not exist"))

        cash_from = get_cash(username)
        cash_to = get_cash(transfer_to)
        bank_cash = get_cash("BANK")

        update_account("BANK", bank_cash + 1)
        update_account(transfer_to, cash_to + money-1)
        update_account(username, cash_from - money)

        return jsonify(generate_return_dictionary(200, "transfer success"))


class Balance(Resource):
    def post(self):
        postedDate = request.get_json()
        username = postedDate["username"]
        password = postedDate["password"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        # using mongo db project, used to hide some attributes of a user returned from the database
        retJson = users.find({"Username": username}, {"Password": 0, "_id": 0})[0]
        return jsonify(retJson)


class TakeLoan(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        # check the value of the loan amount taken
        # if money <= 0 return cannot take a loan less than or equals 0

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = get_cash(username)
        debt = find_user_debt(username)

        update_account(username, cash + money)

        return jsonify(generate_return_dictionary(200, "loan successful"))


class PayLoan(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verify_credentials(username, password)
        if error:
            return jsonify(retJson)

        cash = get_cash(username)

        if cash < money:
            return jsonify(generate_return_dictionary(303, "Insufficient balance"))

        debt = find_user_debt(username)

        update_account(username, cash - money)
        update_debt(username, debt - money)

        return jsonify(generate_return_dictionary(200, "Loan successfully paid"))


api.add_resource(Register, "/register")
api.add_resource(Add, "/add")
api.add_resource(Transfer, "/transfer")
api.add_resource(TakeLoan, "/takeloan")
api.add_resource(PayLoan, "/payloan")
api.add_resource(Balance, "/balance")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    












