# routes/votes.py

from flask import Blueprint, request, jsonify
from app import mysql

votes = Blueprint('votes', __name__)

@votes.route('/', methods=['POST'])
def save_vote():
    data = request.json
    tournament_id = data['tournament_id']
    winner_id = data['winner_id']
    loser_id = data['loser_id']
    round_num = data['round']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO votes (tournament_id, winner_id, loser_id, round)
        VALUES (%s, %s, %s, %s)
    """, (tournament_id, winner_id, loser_id, round_num))
    mysql.connection.commit()
    return jsonify({'result': 'success'})

@votes.route('/<int:tournament_id>', methods=['GET'])
def get_votes(tournament_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT winner_id, loser_id, round, created_at
        FROM votes
        WHERE tournament_id = %s
        ORDER BY round ASC, created_at ASC
    """, (tournament_id,))
    rows = cursor.fetchall()
    return jsonify(rows)
