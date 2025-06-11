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
        response = requests.post("http://localhost:9000/create_tournament", json=blockchain_payload)
        response.raise_for_status()

        contract_data = response.json()
        contract_address = contract_data.get("contract_address")

        if contract_address:
            conn = get_db(db_path)
            cur = conn.cursor()
            cur.execute("UPDATE tournaments SET contract_address = ? WHERE tournament_id = ?",(contract_address, tournament_id))
            conn.commit()
            conn.close()
        else:
            print("contract_address가 응답에 없음")

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
    # 이때 contract_address는 비워짐
    return jsonify({"status": "Success", "tournament_id": tournament_id})

# tournaments 전체 조회
@tournaments.route("/tournaments", methods=["GET"])
def list_tournaments_route():
    db_path = current_app.config['DB_PATH']
    return jsonify({"tournaments":list_tournaments(db_path)})

@tournaments.route("/<int:tournament_id>", methods=["GET"])
def get_tournament_detail(tournament_id):
    db_path = current_app.config['DB_PATH']
    conn = get_db(db_path)
    cur = conn.cursor()

    # 1. 토너먼트 정보 조회
    cur.execute("SELECT * FROM tournaments WHERE tournament_id = ?", (tournament_id,))
    tournament = cur.fetchone()

    if not tournament:
        conn.close()
        return jsonify({"error": "Tournament not found"})

    # 2. 후보 정보 조회
    cur.execute("SELECT * FROM candidates WHERE tournament_id = ?", (tournament_id,))
    candidates = [dict(row) for row in cur.fetchall()]
    conn.close()

    # 3. 응답 구성
    tournament_data = dict(tournament)
    tournament_data["candidates"] = candidates

    return jsonify(tournament_data)