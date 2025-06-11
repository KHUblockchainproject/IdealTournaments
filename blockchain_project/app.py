from flask import Flask, request, jsonify
from routes.candidates  import candidates
from routes.tournaments import tournaments

app = Flask(__name__)
app.config['DB_PATH'] = 'blockchain_project/db/tournament.db'

# 라우터 등록
app.register_blueprint(candidates, url_prefix='/api/candidates')
app.register_blueprint(tournaments, url_prefix='/api/tournaments')

if __name__ == '__main__':
    app.run(debug=True)