from flask import Flask, render_template

app = Flask(__name__)

#Links my python to my home html
@app.route("/")
def home():
    return render_template('home.html')

@app.route("/players")
def players():
    return render_template("players.html")

@app.route("/teams")
def teams():
    return render_template("teams.html")


if __name__ == "__main__":
    app.run(debug=True)