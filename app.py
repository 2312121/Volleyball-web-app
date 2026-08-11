import sqlite3, os

from flask import Flask, render_template, g, session, redirect, url_for, request

DATABASE = 'database.db'

UPLOAD_FOLDER = "static/images"

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

#Links my python to my home html and auto loads articles
@app.route("/")
def home():

    cursor = get_db().cursor()
    cursor.execute("""SELECT * FROM news ORDER BY newsID DESC LIMIT 1""")

    article = cursor.fetchone()

    return render_template("home.html", article=article)


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


#error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

#this route acccepts get AND posts
@app.route('/login', methods=["GET","POST"])
def login():
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
            return redirect("/admin")
        else:
            return render_template("login.html", error="Incorrect username or password")

    return render_template("login.html")


@app.route("/admin")
def admin():


    if session.get("username") != "admin":
        print("Not logged in")
        return redirect("/login")

    return render_template("admin.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/player/add", methods=["GET", "POST"])
def add_player():

    #Make sure the user is logged in
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":

        playername = request.form["playername"]
        teamID = request.form["teamID"]
        height = request.form["height"]
        position = request.form["position"]
        playerimage = request.form["playerimage"]
        weight = request.form["weight"]

        db = get_db()

        db.execute("""INSERT INTO players (teamID, playername, height, position, playerimage, weight) 
                   VALUES (?, ?, ?, ?, ?, ?)""", (
            teamID,
            playername,
            height,
            position,
            playerimage,
            weight,
        ))

        db.commit()
        return redirect(url_for("admin"))

    #Get teams for the dropdown
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM teams")
    teams = cursor.fetchall()

    return render_template("add_player.html", teams=teams)



@app.route("/admin/results", methods=["GET", "POST"])
def manage_results():

    #Make sure only the admin can access this
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":

        homeTeam = request.form["homeTeam"]
        awayTeam = request.form["awayTeam"]
        homeSets = request.form["homeSets"]
        awaySets = request.form["awaySets"]

        db = get_db()

        db.execute("""
            INSERT INTO matches
            (homeTeam, awayTeam, homeSets, awaySets)
            VALUES (?, ?, ?, ?)
        """, (homeTeam, awayTeam, homeSets, awaySets))

        db.commit()

        return redirect(url_for("manage_results"))

    #Get all teams for the dropdown menus
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM teams")
    teams = cursor.fetchall()

    return render_template("manage_results.html", teams=teams)


@app.route("/admin/news", methods=["GET", "POST"])
def manage_news():

    # Only allow the admin to access this page
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"]
        category = request.form["category"]
        description = request.form["description"]
        content = request.form["content"]

        # Get the uploaded image
        image = request.files["image"]

        # Save the image into static/images
        image.save(
            os.path.join(UPLOAD_FOLDER, image.filename)
        )

        # Save the article information into the database
        db = get_db()

        db.execute("""
            INSERT INTO news
            (title, description, content, image, category)
            VALUES (?, ?, ?, ?, ?)
            """, (
                title,
                description,
                content,
                image.filename,
                category
            ))

        db.commit()

        return redirect(url_for("admin"))

    return render_template("manage_news.html")


@app.route("/news/<int:newsID>")
def article(newsID):

    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM news WHERE newsID = ?",(newsID,))

    article = cursor.fetchone()

    if article is None:
        return render_template("404.html"), 404

    return render_template(
        "article.html",
        article=article
    )

@app.route("/admin/players")
def manage_players():

    #Make sure only the admin can access this page
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    cursor = get_db().cursor()
    cursor.execute("""
        SELECT *
        FROM players
        JOIN teams ON players.teamID = teams.teamID""")

    players = cursor.fetchall()

    return render_template("manage_players.html", players=players)

@app.route("/admin/player/delete/<int:playerID>", methods=["POST"])
def delete_player(playerID):

    #Make sure only the admin can delete players
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "DELETE FROM players WHERE playerID = ?",(playerID,))
    db.commit()

    return redirect(url_for("manage_players"))


if __name__ == "__main__":
    app.run(debug=True)