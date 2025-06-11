import sqlite3

# DB 경로 (app.py와 동일하게)
db_path = "db/tournament.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. 토너먼트 더미 데이터
cursor.execute("""
INSERT INTO tournaments (tournament_title, description, wallet_address, thumbnail, contract_address)
VALUES (?, ?, ?, ?, ?)
""", (
    "아이돌 이상형 월드컵",
    "최애를 골라보세요!",
    "0xabc123",
    "https://example.com/thumb.jpg",
    "0xCONTRACT123"
))
tournament_id = cursor.lastrowid

# 2. 후보자 더미 데이터
candidates = [
    ("아이유", "https://example.com/iu.jpg"),
    ("제니", "https://example.com/jennie.jpg"),
    ("장원영", "https://example.com/jang.jpg"),
]

for name, image_url in candidates:
    cursor.execute("""
    INSERT INTO candidates (tournament_id, candidate_name, image_url)
    VALUES (?, ?, ?)
    """, (tournament_id, name, image_url))

conn.commit()
conn.close()

print(f"✅ 테스트 데이터 삽입 완료 (tournament_id = {tournament_id})")
