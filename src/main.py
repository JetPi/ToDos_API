"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, Todos
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
db_url = os.getenv('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/todos', methods=['GET'])
def handle_todos():
    if request.method == 'GET':
        todos = Todos.query.all()
        return jsonify(list(map(lambda item: item.serialize(), todos))), 200

@app.route('/todos', methods=['POST'])
def add_new_user():
    if request.method == 'POST':
        body = request.json

        if body.get("label") is None:
            return jsonify({"message": "Error, property bad"}), 400 
        elif body.get("done") is None:
            return jsonify({"message": "Error, property bad"}), 400

        new_todo = Todos(label=body.get("label"), done=body.get("done"))
        db.session.add(new_todo)

        try:
            db.session.commit()
            return jsonify(new_todo.serialize()), 201
        except Exception as error:
            print(error.args)
            db.session.rollback()
            return jsonify({"message": f"Error {error.args}"}), 500

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_user(todo_id = None):
    if request.method == 'DELETE':
        if todo_id is None:
            return jsonify({"message": "Error, bad request"}), 400
        elif todo_id is not None:
            deleted_todo = Todos.query.get(todo_id)
            if deleted_todo is None:
                return jsonify({"message": "Error, couldn't find user"}), 404
            else:
                db.session.delete(deleted_todo)

            try:
                db.session.commit()
                return jsonify([]), 204
            except Exception as error:
                print(error.args)
                db.session.rollback()
                return jsonify({"message": f"Error {error.args}"})

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
