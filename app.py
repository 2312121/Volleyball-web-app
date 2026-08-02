import sqlite3

from flask import Flask, render_template, g, session, redirect, url_for, request

DATABASE = 'database.db'

app = Flask(__name__)

app.config['SECRET_KEY'] = "MySecretKey"

# these are stored server side when hosted. But this is the LEAST secure login method
# hard coded username and passwords to access the 'admin" part of the site 
USERNAME = "admin"
PASSWORD = "admin"

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
    print("hello world?")
    return render_template('home.html')


#links my python to my players page
@app.route("/players")
def players():
    #Do query get results back send to template
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM players JOIN teams ON players.teamID=teams.teamID ORDER BY weight DESC")
    results = cursor.fetchall()
    return render_template("players.html", results = results)

#links my ladder page to my python and creates the ladder table
@app.route("/ladder")
def ladder():
    cursor = get_db().cursor()
    cursor.execute("""SELECT * FROM teams ORDER BY wins DESC, ("for" - against) DESC """)
    results = cursor.fetchall()
    print(results)
    return render_template("ladder.html", results = results)

#links my player page for each individual player to my python and creates the ladder table
@app.route("/player/<int:playerID>")
def player(playerID):

    cursor = get_db().cursor()

    cursor.execute("""
        SELECT * FROM players JOIN teams ON players.teamID = teams.teamID WHERE playerID = ? """, (playerID,))
    player = cursor.fetchone()

    return render_template("player.html", player=player)

#for home page article
@app.route("/news/spikers-16-0")
def spikers_article():
    return render_template("spikers_article.html")

#error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

#this route acccepts get AND posts
@app.route('/login', methods=["GET","POST"])
def index_post():
    #if we are posting to the route do this stuff
    if request.method == "POST":
        #get the username from the form
        username = request.form['username']
        password = request.form['password']
        #check them here
        if username == USERNAME and password == PASSWORD:
            #we successfully logged in
            #store the username in the session- it's a dictionary that is visible everywhere
            #for the entire time this user has the app open in browser- clears when the close the browser
            session['username'] = username
            return redirect("/index")
        else:
            return render_template("login.html", error="Incorrect username or password")

    return render_template("login.html")

@app.route("/admin")
def admin():

    if "username" not in session:
        return redirect("/login")

    return render_template("admin.html")



if __name__ == "__main__":
    app.run(debug=True)