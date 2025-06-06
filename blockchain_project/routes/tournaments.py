# routes/tournaments.py

from flask import Blueprint, request, jsonify, current_app
import sqlite3

tournaments_bp = Blueprint('tournaments', __name__)

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_tournament(data, db_path):
    title = data["Tournament_title"]
    desc = data["Description"]
    wallet = data["Wallet_address"]
    thumb = data["Thumbnail"]
    candidates = data["Candidates"]
    contract_address = data["Contract_address"]

    conn = get_db(db_path)
    cur = conn.cursor()

    cur.execute("INSERT INTO tournaments (title, description, wallet_address, thumbnail) VALUES (?, ?, ?, ?)",
                (title, desc, wallet, thumb))
    tournament_id = cur.lastrowid

    for c in candidates:
        cur.execute("INSERT INTO candidates (tournament_id, candidate_name, image_url) VALUES (?, ?, ?)",
                    (tournament_id, c["Candidate_Name"], c["Image_url"]))

    conn.commit()
    conn.close()

    return tournament_id

def list_tournaments(db_path):
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tournaments")
    result = [dict(row) for row in cur.fetchall()]
    conn.close()
    return result

@tournaments_bp.route("/create_tournament", methods=["POST"])
def create_tournament_route():
    data = request.json
    db_path = current_app.config['DB_PATH']
    tournament_id = create_tournament(data, db_path)
    return jsonify({"message": "Tournament created", "tournament_id": tournament_id}), 201

@tournaments_bp.route("/tournaments", methods=["GET"])
def list_tournaments_route():
    db_path = current_app.config['DB_PATH']
    return jsonify(list_tournaments(db_path))