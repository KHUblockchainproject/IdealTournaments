# routes/tournaments.py

from flask import Blueprint, request, jsonify, current_app
import sqlite3
import requests

tournaments = Blueprint('tournaments', __name__)

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_tournament(data, db_path):
    title = data["Tournament_title"]
    desc = data["Description"]
    wallet = data["Wallet_address"]
    thumb = data["Thumbnail"]
    contract_address = None
    candidates = data.get("Candidates", [])
    

    conn = get_db(db_path)
    cur = conn.cursor()

    cur.execute("INSERT INTO tournaments (title, description, wallet_address, thumbnail, contract_address) VALUES (?, ?, ?, ?, ?)",
                (title, desc, wallet, thumb, contract_address))
    tournament_id = cur.lastrowid

    for c in candidates:
        cur.execute("INSERT INTO candidates (tournament_id, candidate_name, image_url) VALUES (?, ?, ?)",
                    (tournament_id, c["Candidate_Name"], c["Image_url"]))

    conn.commit()
    conn.close()

    try:
        blockchain_payload = {
            "tournament_id": tournament_id,
            "wallet_address": wallet
        }
        # 블록체인 서버의 토너먼트 deploy endpoint
        response = requests.post("http://BLOCKCHAIN_SERVER_ADDRESS/deploy", json=blockchain_payload)
        response.raise_for_status()
    except Exception as e:
        print("블록체인 서버 호출 실패", e)
    

    return tournament_id

def list_tournaments(db_path):
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tournaments")
    result = [dict(row) for row in cur.fetchall()]
    conn.close()
    return result

#tournaments 생성
@tournaments.route("/create_tournament", methods=["POST"])
def create_tournament_route():
    data = request.json
    db_path = current_app.config['DB_PATH']
    tournament_id = create_tournament(data, db_path)
    # 이때 contract_address는 비워짐짐
    return jsonify({"status": "Success", "tournament_id": tournament_id}), 201

# tournaments 전체 조회
@tournaments.route("/tournaments", methods=["GET"])
def list_tournaments_route():
    db_path = current_app.config['DB_PATH']
    return jsonify(list_tournaments(db_path))

# 블록체인 서버로부터 deploy한 contract의 address를 받음
@tournaments.route("/update_contract", methods=["POST"])
def update_contract_address():
    data = request.get_json()
    tournament_id = data.get("tournament_id")
    contract_address = data.get("contract_address")

    if not tournament_id or not contract_address:
        return jsonify({"error": "tournament_id and contract_address required"}), 400

    db_path = current_app.config['DB_PATH']
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE tournaments SET contract_address = ? WHERE tournament_id = ?", (contract_address, tournament_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Contract address updated"}), 200