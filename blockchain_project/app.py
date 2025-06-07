from flask import Flask, request, jsonify
from routes.candidates  import candidates
from routes.tournaments import tournaments
from routes.votes import votes

app = Flask(__name__)
app.config['DB_PATH'] = 'db/tournament.db'

# 라우터 등록
# app.register_blueprint(candidates, url_prefix='/api/candidates')
app.register_blueprint(tournaments, url_prefix='/api/tournaments')
app.register_blueprint(votes, url_prefix='/api/votes')

if __name__ == '__main__':
    app.run(debug=True)