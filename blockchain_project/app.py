from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from routes.candidates  import candidates
from routes.tournaments import tournaments
from routes.votes import votes
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1223'
app.config['MYSQL_DB'] = 'ideal_worldcup'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# 라우터 등록
app.register_blueprint(candidates, url_prefix='/api/candidates')
app.register_blueprint(tournaments, url_prefix='/api/tournaments')
app.register_blueprint(votes, url_prefix='/api/votes')

if __name__ == '__main__':
    app.run(debug=True)