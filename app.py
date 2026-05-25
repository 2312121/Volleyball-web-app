from flask import Flask, render_template

app = Flask(__name__)

#Links my python to my home html
@app.route("/")
def home():
    return render_template('home.html')


if __name__ == "__main__":
    app.run(debug=True)