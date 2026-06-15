import sqlite3

from flask import Flask, render_template, g

DATABASE = 'database.db'

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#Links my python to my home html
@app.route("/")
def home():
    return render_template('home.html')

#links my python to my players page
@app.route("/players")
def players():
    #Do query get results back send to template
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM players JOIN teams ON players.teamID=teams.teamID")
    results = cursor.fetchall()
    return render_template("players.html", results = results)

#links my team page to my python 
@app.route("/teams")
def teams():
    return render_template("teams.html")



if __name__ == "__main__":
    app.run(debug=True)