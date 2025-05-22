# routes/tournaments.py

from flask import Blueprint, request, jsonify
from app import mysql

tournaments = Blueprint('tournaments', __name__)

@tournaments.route('/', methods=['GET'])
def get_tournaments():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, title, description FROM tournaments")
    rows = cursor.fetchall()
    return jsonify(rows)

@tournaments.route('/', methods=['POST'])
def create_tournament():
    data = request.json
    title = data.get('title')
    description = data.get('description', '')

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO tournaments (title, description) VALUES (%s, %s)", (title, description))
    mysql.connection.commit()
    return jsonify({'result': 'success', 'tournament_id': cursor.lastrowid})
