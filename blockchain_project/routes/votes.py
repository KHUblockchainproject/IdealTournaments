# routes/votes.py

from flask import Blueprint, request, jsonify, current_app
import sqlite3
import requests

votes = Blueprint('votes', __name__)

def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@votes.route("/vote", methods=["POST"])
def vote():
    data = request.get_json()
    tournament_id = data.get("Tournament_id")
    candidate_id = data.get("Candidate_id")
    wallet_address = data.get("Wallet_address")

    if not (tournament_id and candidate_id and wallet_address):
        return jsonify({"error": "Missing required fields"}), 400

    # 1. DB에서 contract_address 조회
    db_path = current_app.config['DB_PATH']
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("SELECT contract_address FROM tournaments WHERE tournament_id = ?", (tournament_id,))
    row = cur.fetchone()
    conn.close()

    if not row or not row["contract_address"]:
        return jsonify({"error": "Tournament or contract not found"}), 404

    contract_address = row["contract_address"]

    # 2. 블록체인 투표 서버로 전달할 payload 구성
    payload = {
        "tournament_id": tournament_id,
        "contract_address": contract_address,
        "candidate_id": candidate_id,
        "wallet_address": wallet_address
    }

    try:
        # 3. 투표 처리 서버에 요청 전송
        response = requests.post("http://localhost:9000/vote", json=payload)
        response.raise_for_status()
        # 응답에 대해 사용자로 콜백
        result = response.json()
        return jsonify(result), 200
    
        #디버깅용용
        #return jsonify(payload)
    except Exception as e:
        print("블록체인 서버 호출 실패:", e)
        return jsonify({"error": "Blockchain vote failed"}), 500

@votes.route("/check_voted", methods=["POST"])
def check_vote():
    data = request.get_json()
    tournament_id = data.get("tournament_id")
    wallet_address = data.get("wallet_address")

    if not tournament_id or not wallet_address:
        return jsonify({"error": "Missing tournament_id or wallet_address"}), 400

    db_path = current_app.config['DB_PATH']
    conn = get_db(db_path)
    cur = conn.cursor()

    # 1. contract_address 조회
    cur.execute("SELECT contract_address FROM tournaments WHERE tournament_id = ?", (tournament_id,))
    row = cur.fetchone()
    conn.close()

    if not row or not row["contract_address"]:
        return jsonify({"error": "Tournament or contract address not found"}), 404

    contract_address = row["contract_address"]

    # 2. 투표 처리 서버로 요청
    try:
        payload = {
            "tournament_id": tournament_id,
            "contract_address": contract_address,
            "wallet_address": wallet_address
        }

        response = requests.post("http://localhost:9000/isVoted", json=payload)
        response.raise_for_status()
        result = response.json()

        # 3. 사용자에게 그대로 응답

        return jsonify(result), 200
        #return jsonify(payload), 200
    except Exception as e:
        print("투표처리서버 요청 실패:", e)
        return jsonify({"error": "Vote check failed"}), 500
@votes.route("/vote_query",methods=["POST"])
def vote_query():
    data = request.get_json()
    tournament_id = data["tournament_id"]
    if not tournament_id:
        return jsonify({"error": "Missing tournament_id"}), 400

    db_path = current_app.config['DB_PATH']
    conn = get_db(db_path)
    cur = conn.cursor()

    cur.execute("SELECT contract_address FROM tournaments WHERE tournament_id = ?", (tournament_id,))
    row = cur.fetchone()
    if not row or not row["contract_address"]:
        return jsonify({"error": "Tournament or contract address not found"}), 404

    cur.execute("SELECT COUNT(*) AS total FROM candidates WHERE tournament_id = ?", (tournament_id,))
    count_row = cur.fetchone()
    conn.close()

    total_candidate_count = count_row["total"] if count_row else 0

    contract_address = row["contract_address"]
    try:
        payload = {
            "contract_address": contract_address,
            "totalCandidateCount":  total_candidate_count
        }

        response = requests.post("http://localhost:9000/results",json=payload)
        response.raise_for_status()
        response_data = response.json()
    except Exception as e:
        print("투표 수 조회 실패", e)
        return jsonify({"error": "Vote query failed"})
    return jsonify({
        "status": response_data.get("status", "Unknown"),
        "totalVotes": response_data.get("totalVotes",[])
    })