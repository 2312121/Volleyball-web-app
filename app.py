import sqlite3, os

from flask import Flask, render_template, g, session, redirect, url_for, request

DATABASE = 'database.db'

UPLOAD_FOLDER = "static/images"

app = Flask(__name__)

app.config['SECRET_KEY'] = "MySecretKey"

#These are stored server side when hosted. But this is the LEAST secure login method
#Hard coded username and passwords to access the 'admin" part of the site 
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

    if session.get("username") != "admin":
        return redirect(url_for("login"))

    db = get_db()

    cursor = db.cursor()

    #Get the teams
    cursor.execute("SELECT teamID, teamname FROM teams")
    teams = cursor.fetchall()
    

    if request.method == "POST":

        playername = request.form["playername"]
        height = request.form["height"]
        position = request.form["position"]
        weight = request.form["weight"]
        teamID = request.form["teamID"]

        playerimage = request.files["playerimage"]

        playerimage.save(
            os.path.join("static/images", playerimage.filename)
        )

        db.execute("""
            INSERT INTO players
            (teamID, playername, height, position, playerimage, weight)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            teamID,
            playername,
            height,
            position,
            playerimage.filename,
            weight
        ))

        db.commit()

        return redirect(url_for("admin"))

    return render_template("add_player.html", teams=teams)

    #Send teams to the HTML page
    return render_template("add_player.html", teams=teams)
    

    #Get teams for the dropdown
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM teams")
    teams = cursor.fetchall()

    return render_template("add_player.html", teams=teams)



@app.route("/admin/results", methods=["GET", "POST"])
def manage_results():

    if session.get("username") != "admin":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    #Get teams for the dropdown menus
    cursor.execute("SELECT teamID, teamname FROM teams")
    teams = cursor.fetchall()

    if request.method == "POST":

        team1 = request.form["team1"]
        team2 = request.form["team2"]

        #Make sure the teams aren't the same
        if team1 == team2:

            return render_template(
                "manage_results.html",
                teams=teams,
                error="A team cannot play against itself."
            )

        #Get all five set scores
        set1_team1 = int(request.form["set1_team1"])
        set1_team2 = int(request.form["set1_team2"])

        set2_team1 = int(request.form["set2_team1"])
        set2_team2 = int(request.form["set2_team2"])

        set3_team1 = int(request.form["set3_team1"])
        set3_team2 = int(request.form["set3_team2"])

        #Sets 4 and 5 are optional
        set4_team1 = request.form.get("set4_team1")
        set4_team2 = request.form.get("set4_team2")

        set5_team1 = request.form.get("set5_team1")
        set5_team2 = request.form.get("set5_team2")


        #Convert optional scores into integers
        if set4_team1 != "" and set4_team2 != "":
            set4_team1 = int(set4_team1)
            set4_team2 = int(set4_team2)
        else:
            set4_team1 = None
            set4_team2 = None


        if set5_team1 != "" and set5_team2 != "":
            set5_team1 = int(set5_team1)
            set5_team2 = int(set5_team2)
        else:
            set5_team1 = None
            set5_team2 = None


        #Store all scores in a list
        sets = [
            (set1_team1, set1_team2),
            (set2_team1, set2_team2),
            (set3_team1, set3_team2)
        ]

        if set4_team1 is not None:
            sets.append((set4_team1, set4_team2))

        if set5_team1 is not None:
            sets.append((set5_team1, set5_team2))


        #Count how many sets each team won
        team1_sets = 0
        team2_sets = 0

        #Add up all the total points
        team1_points = 0
        team2_points = 0


        for score1, score2 in sets:

            team1_points += score1
            team2_points += score2

            if score1 > score2:
                team1_sets += 1

            elif score2 > score1:
                team2_sets += 1


        #Make sure there is a winner of the match 
        if team1_sets == team2_sets:

            return render_template(
                "manage_results.html",
                teams=teams,
                error="The match must have a winner."
            )


        #Team 1 won
        if team1_sets > team2_sets:

            winner = team1
            loser = team2

        #Team 2 won
        else:

            winner = team2
            loser = team1


        #Add points for Team 1
        db.execute("""
            UPDATE teams

            SET "for" = "for" + ?,
                against = against + ?

            WHERE teamID = ?
        """, (
            team1_points,
            team2_points,
            team1
        ))


        #Add points for Team 2
        db.execute("""
            UPDATE teams

            SET "for" = "for" + ?,
                against = against + ?

            WHERE teamID = ?
        """, (
            team2_points,
            team1_points,
            team2
        ))


        #Add one win to the winner
        db.execute("""
            UPDATE teams

            SET wins = wins + 1

            WHERE teamID = ?
        """, (winner,))


        #Add one loss to the loser
        db.execute("""
            UPDATE teams

            SET loses = loses + 1

            WHERE teamID = ?
        """, (loser,))


        #Save everything
        db.commit()

        return redirect(url_for("admin"))


    return render_template("manage_results.html", teams=teams)



@app.route("/admin/news", methods=["GET", "POST"])
def manage_news():

    #Make sure only the admin can access this page
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    #If the form was submitted
    if request.method == "POST":

        #Get the text from the form
        title = request.form["title"]
        description = request.form["description"]
        content = request.form["content"]
        category = request.form["category"]

        #Get the uploaded image
        image = request.files["image"]

        #Save the image into static/images
        image.save(
            os.path.join("static/images", image.filename)
        )

        #Connect to the database
        db = get_db()

        #Add the article information to the news table
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

        #Save the changes to the database
        db.commit()

        #Go back to the admin page
        return redirect(url_for("admin"))

    #Show the form
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



@app.route("/admin/articles")
def manage_articles():

    #Only allow the admin
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    cursor = get_db().cursor()

    cursor.execute("""
        SELECT *
        FROM news
        ORDER BY newsID DESC
    """)

    articles = cursor.fetchall()

    return render_template(
        "manage_articles.html",
        articles=articles
    )

@app.route("/admin/article/delete/<int:newsID>", methods=["POST"])
def delete_article(newsID):

    #Only allow logged-in admin
    if session.get("username") != "admin":
        return redirect(url_for("login"))

    db = get_db()

    #Delete the article from the database
    db.execute(
        "DELETE FROM news WHERE newsID = ?",
        (newsID,)
    )

    #Save the change
    db.commit()

    return redirect(url_for("manage_articles"))


if __name__ == "__main__":
    app.run(debug=True)