from flask import Flask, request, render_template, redirect, url_for, session\
, Response, jsonify
from storysheet import StorySheet
from oauth2client.service_account import ServiceAccountCredentials
import time
from flask_cors import CORS

# define the scope
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

# authenticate using the service account JSON key

creds = ServiceAccountCredentials.from_json_keyfile_name("/home/lurch5-64/progamming/jogodehistorias/creds/jogodehistorias-beta-e6e6f9107f08.json", scope)

storybase = StorySheet (creds, "rigmarole-testing", "stories")
# TODO: use session to store user data to use in retrieval of stories from the google sheet.

ROOM_ID = storybase.get_metadata()["room_id"]

app = Flask(__name__)
CORS (app)
# I'm not sure if we ever need to use this secret key...
#   so i'll make it a hash.
app.secret_key = f"{hash('rigmarole')}"

@app.route("/login-page")
def login_page () :
    return render_template("login-page.html")

@app.route("/login-request", methods=["POST"])
def login_request () :
    username = request.form["username"]
    room_id = request.form["room-id"]
    session["username"] = username
    if str(room_id) != ROOM_ID:
        return render_template("login-page.html")
    elif str(room_id) == ROOM_ID:
        # we're in!
        # code for entering the room
        storybase.add_new_user (session.get("username"))
        return redirect(url_for("writing_page"))

@app.route("/writing-page", methods=["POST", "GET"])
def writing_page () :
    if request.method == "POST":
        # pull text from the textarea
        story_addition = request.form['story-addition']

        print (story_addition) # debuggin
        # TODO: spit this out on the google sheets
        return redirect(url_for("game_start_waiting"))
    else:
        # DEBUGGING ONLY:
        target_storyid = storybase.get_target_storyid(session.get("username"))
        target_story_todate = storybase.get_current_story(target_storyid)
        # TODO manage first round and special instructions (like if this is the
        #   last round and we need to finish things up)
        return render_template('writing-page.html', previous_story=target_story_todate)

@app.route("/create-room", methods=["POST", "GET"])
def create_room () :
    if request.method == "POST":
        username = request.form["username"]
        new_room_id = abs(hash(str(username)))
        storybase.insert_room_id (new_room_id)
        storybase.set_owner (username)
        return render_template ('create-room.html', room_id=new_room_id)
    else:
        return redirect(url_for("login_page"))

@app.route("/wait/round-to-finish")
def round_finish_waiting () :
    return render_template ('round-finish-waiting.html')

@app.route("/wait/game-to-start")
def game_start_waiting () :
    owner = storybase.get_metadata()["owner"]

    return render_template ('game-start-waiting.html', room_owner=owner)

@app.route("/player-count-updates")
def get_updates () :
    num_players = storybase.count_players ()
    data = f"players in room: {num_players}"
    return jsonify ({"message": data})

@app.route("/start-game", methods=["POST"])
def start_game () :
    if request.method == "POST":
        # do something about room starting
        storybase.set_accepting_new_players(False)
        return redirect(url_for("writing_page"))

@app.route("/check-game-start", methods=["GET"])
def check_game_start () :
    # did the game start?
    game_started = storybase.get_metadata()["game_started"]
    print (type(game_started))
    print (game_started)
    return jsonify ({"redirect": game_started})

if __name__ == "__main__":
    app.run(debug=True)