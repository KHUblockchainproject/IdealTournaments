from flask import Blueprint, request, jsonify
from app import mysql

candidates = Blueprint('candidates', __name__)

@candidates.route('/<int:tournament_id>', methods=['GET'])
def get_candidates(tournament_id):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.image_url
        FROM candidates c
        JOIN tournament_candidates tc ON c.id = tc.candidate_id
        WHERE tc.tournament_id = %s
    """, (tournament_id,))
    rows = cursor.fetchall()
    return jsonify(rows)
