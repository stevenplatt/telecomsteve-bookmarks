# Instructions for deployment to AWS Elastic Beanstalk
# https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html
# push updated deployment using 'eb deploy' from within the folder telecomsteve/

import requests, os, pathlib, google.auth.transport.requests
from flask import Flask, session, abort, request, render_template, redirect
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from pip._vendor import cachecontrol

app = Flask("Telecomsteve Bookmarks")
app.secret_key = "telecomsteve.com"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "217176846725-3dugl7nut15ilfq30n7rce0ne47hapur.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file = client_secrets_file,
    scopes = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri = "http://127.0.0.1:5000/callback"
)

def login_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401) # authorization required
        else: 
            return function()
    return wrapper

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500) # state does not match

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session = cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token = credentials._id_token,
        request = token_request,
        audience = GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/protected_area")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/")
def index():
    return render_template("login.html")
    # return "Hello World <a href = '/login'><button>Login</button></a>"

@app.route("/protected_area")
@login_required
def protected_area():
    user = session['name']
    return render_template("index.html", name=user)
    # return f"Hello {session['name']}! <br/> <a href = '/logout'><button>Logout</button></a>"


# run the app.
if __name__ == "__main__":
    app.run (debug=False) # (host= '0.0.0.0') host="localhost", port=8000, 
