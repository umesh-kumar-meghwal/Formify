from flask import Flask, render_template, request


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")

@app.route('/transform',methods=["POST","GET"])
def transform():
    if request.method=="POST":
        return render_template('transform.html')
    else:
        return render_template('transform.html')
        
        
        
 

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )