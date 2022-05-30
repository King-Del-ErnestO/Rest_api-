from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS 
from bson import ObjectId
import jwt
from datetime import datetime, timedelta
from functools import wraps
import os


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = "srfxfhxgxjjxjxgxxggzfhxjgujg"

mongo = MongoClient("mongodb+srv://quickwork:quickwork@users.46fhmfp.mongodb.net/?retryWrites=true&w=majority")
db = mongo.test


#REGISTER
@app.route('/register', methods=['POST'])
def save_user():
    message = ""
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        check = db['users']
        if check.count_documents({"email": data['email']}) >= 1:
            message = "user with that email exists"
            code = 401
            status = "fail"
        else:
            data['created'] = datetime.now()

            res = db["users"].insert_one(data)
            if res.acknowledged:
                status = "successful"
                message = "user created successfully"
                code = 201
    except Exception as ex:
        message = f"{ex}"
        status = "fail"
        code = 500
    return jsonify({'status': status, "message": message}), code

#LOGIN
@app.route('/login', methods=['POST'])
def login():
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        user = db['users'].find_one({"email": f'{data["email"]}'})

        if user:
            user['_id'] = str(user['_id'])
            email = user["email"]
            if user:
                time = datetime.utcnow() + timedelta(hours=24)
                token = jwt.encode({
                        "user": {
                            "email": f"{user['email']}",
                            "id": f"{user['_id']}",
                        },
                        "exp": time
                    }, app.secret_key, algorithm="HS256")

                res = db['users'].update_one({"email": email}, {"$set":{'email':user['email'], 'password':user['password'], 'first_name':user['first_name'], 'last_name':user["last_name"], 'token':token}})
                message = f"user authenticated"
                code = 200
                status = "successful"
                res_data['token'] = token
                res_data['user'] = (lambda token, **kw:kw)(**user)

            else:
                message = "wrong password"
                code = 401
                status = "fail"
        else:
            message = "invalid login details"
            code = 401
            status = "fail"

    except Exception as ex:
        message = f"{ex}"
        code = 500
        status = "fail"
    return jsonify({'status': status, "data": res_data, "message":message}), code

#Login JWT Token Verification
def tokenReq(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "Authorization" in request.headers:
            token = request.headers['Authorization']
            token = str.replace(str(token), 'Bearer ', '')
            try:
                jwt.decode(token, app.secret_key, algorithms="HS256")
            except:
                return jsonify({"status": "fail", "message": "Not same"}), 401
            return f(*args, **kwargs)
        else:
            return jsonify({"status": "fail", "message": "unauthorized"}), 401

    return decorated


#TEMPLATE CRUD

# GET ALL and INSERT NEW TEMPLATE
@app.route('/template', methods=['GET', 'POST'])
@tokenReq
def index():
    res = []
    code = 500
    status = "fail"
    message = ""
    token = request.headers['Authorization']
    token = str.replace(str(token), 'Bearer ', '')
    user = db['users'].find_one({"token": token})
    userid = str(user['_id'])
    template = str(f"template {userid}")
    user_template = db[template]
    try:
        if (request.method == 'POST'):
            res = user_template.insert_one(request.get_json())
            if res.acknowledged:
                message = "item saved"
                status = 'successful'
                code = 201
                res = {"_id": f"{res.inserted_id}"}
            else:
                message = "insert error"
                res = 'fail'
                code = 500
        else:
            for r in user_template.find().sort("_id", -1):
                r['_id'] = str(r['_id'])
                res.append(r)
            if res:
                message = "template retrieved"
                status = 'successful'
                code = 200
            else:
                message = "no template found"
                status = 'successful'
                code = 200
    except Exception as ee:
        res = {"error": str(ee)}
    return jsonify({"status":status,'data': res, "message":message}), code


#DELETE SINGLE TEMPLATE
@app.route('/template/<item_id>', methods=['DELETE'])
@tokenReq
def delete_one(item_id):
    data = {}
    code = 500
    message = ""
    status = "fail"
    token = request.headers['Authorization']
    token = str.replace(str(token), 'Bearer ', '')
    user = db['users'].find_one({"token": token})
    userid = str(user['_id'])
    template = str(f"template {userid}")
    user_template = db[template]
    try:
        if (request.method == 'DELETE'):
            res = user_template.delete_one({"_id": ObjectId(item_id)})
            if res:
                message = "Delete successfully"
                status = "successful"
                code = 201
            else:
                message = "Delete failed"
                status = "fail"
                code = 404
        else:
            message = "Delete Method failed"
            status = "fail"
            code = 404
           
    except Exception as ee:
        message = str(ee)
        status = "Error"

    return jsonify({"status": status, "message":message,'data': data}), code


#GET SINGLE TEMPLATE AND UPDATE SINGLE TEMPLATE
@app.route('/template/<item_id>', methods=['GET', 'PUT'])
@tokenReq
def by_id(item_id):
    data = {}
    code = 500
    message = ""
    status = "fail"
    token = request.headers['Authorization']
    token = str.replace(str(token), 'Bearer ', '')
    user = db['users'].find_one({"token": token})
    userid = str(user['_id'])
    template = str(f"template {userid}")
    user_template = db[template]
    try:
        if (request.method == 'PUT'):
            res = user_template.update_one({"_id": ObjectId(item_id)}, {"$set": request.get_json()})
            if res:
                message = "updated successfully"
                status = "successful"
                code = 201
            else:
                message = "update failed"
                status = "fail"
                code = 404
        else:
            data = user_template.find_one({"_id": ObjectId(item_id)})
            data['_id'] = str(data['_id'])
            if data:
                message = "item found"
                status = "successful"
                code = 200
            else:
                message = "update failed"
                status = "fail"
                code = 404
    except Exception as ee:
        message = str(ee)
        status = "Error"

    return jsonify({"status": status, "message":message,'data': data}), code



port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port)

