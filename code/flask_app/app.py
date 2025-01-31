from flask import Flask, request, render_template, redirect, url_for, session\
, Response, jsonify
from storysheet import StorySheet
from oauth2client.service_account import ServiceAccountCredentials
import time
from flask_cors import CORS

# define the scope
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

# authenticate using the service account JSON key

creds = ServiceAccountCredentials.from_json_keyfile_name("creds/jogodehistorias-beta-e6e6f9107f08.json", scope)

storybase = StorySheet (creds, "rigmarole-testing", "stories")
# TODO: use session to store user data to use in retrieval of stories from the google sheet.

app = Flask(__name__)
CORS (app)
# I'm not sure if we ever need to use this secret key...
#   so i'll make it a hash.
app.secret_key = f"{hash('rigmarole')}"
# Now we'll isolate sessions so I can test easier.
app.config['SESSION_COOKIE_NAME'] = f"{hash(time.time())}"
# this should be unique for everyone.

@app.route("/")
def index () :
    return render_template("index.html")

@app.route("/login-page")
def login_page () :
    return render_template("login-page.html")

@app.route("/login-request", methods=["POST"])
def login_request () :
    username = request.form["username"]
    room_id = request.form["room-id"]
    session["username"] = username
    if str(room_id) != str(storybase.get_metadata()["room_id"]):
        return render_template("login-page.html")
    elif str(room_id) == str(storybase.get_metadata()["room_id"]):
        # we're in!
        # code for entering the room
        storybase.add_new_user (session.get("username"))
        # We'll refrain from starting the session counter here
        #   because the admin never sees this route.
        return redirect(url_for("game_start_waiting"))

@app.route("/writing-page", methods=["POST", "GET"])
def writing_page () :
    if request.method == "POST":
        # We're trying to add our part of the story.
        # pull text from the textarea
        story_addition = request.form['story-addition']
        print (story_addition) # debuggin
        target_storyid = storybase.get_target_storyid_round_counter(
            session.get("username"),
            session.get("current_round"))
        storybase.write_target_story(target_storyid,
                                     story_addition=story_addition,
                                     round=session.get("current_round"))
        # TODO: spit this out on the google sheets
        return redirect(url_for("round_finish_waiting"))
    else:
        # We'll try to increment the round counter. If we can't find it,
        #   we'll create the key with a value of 1.
        try:
            session["current_round"] += 1
        except KeyError:
            session["current_round"] = 1
        target_storyid = storybase.get_target_storyid_round_counter (
            session.get("username"),
            session.get("current_round")
        )
        target_story_todate = storybase.get_current_story(target_storyid)
        return render_template (
            'writing-page.html',
            player_name=session.get("username"),
            previous_story=target_story_todate
        )

@app.route("/create-room", methods=["POST", "GET"])
def create_room () :
    if request.method == "POST":
        username = request.form["username"]
        session["username"] = username
        new_room_id = str(abs(hash(str(username))))[-6:]
        storybase.insert_room_id (str(new_room_id))
        storybase.set_owner (username)
        storybase.set_game_started ("FALSE")
        storybase.add_new_user (session.get("username"))
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
        storybase.set_game_started(True)
        return redirect(url_for("writing_page"))

@app.route("/check-game-start", methods=["GET"])
def check_game_start () :
    # did the game start?
    game_started = storybase.get_metadata()["game_started"]
    return jsonify ({"redirect": game_started})

@app.route("/check-round-finished", methods=["GET"])
def check_round_finish () :
    # is the round over (has every body written their story?)
    round_finished = storybase.get_round_over(session.get("current_round"))
    if storybase.get_game_over():
        return jsonify ({"redirect": "GAMEOVER"})
    else:
        return jsonify ({"redirect": round_finished})

@app.route("/review-stories")
def review_stories () :
    stories = storybase.collect_stories ()
    return render_template ("review-stories.html", stories=stories)

if __name__ == "__main__":
    app.run(debug=True)