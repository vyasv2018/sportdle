from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import datetime
import hashlib
from scoring import give_feedback, calculate_elimination_score, calculate_information_score

print("✅ Flask is loading app.py...")

app = Flask(__name__)
CORS(app)

# Load curated solution words
with open("solution_words.txt") as f:
    SOLUTIONS = [w.strip().lower() for w in f if len(w.strip()) == 5]

with open("allowed_guesses.txt") as f:
    ALLOWED_GUESSES = set(w.strip().lower() for w in f if len(w.strip()) == 5)

ALL_VALID_GUESSES = set(SOLUTIONS) | ALLOWED_GUESSES

state = {
    "mode": "infinity",
    "secret": random.choice(SOLUTIONS),
    "remaining_words": SOLUTIONS.copy(),
    "known_letters": set(),
    "known_positions": [None] * 5,
    "yellow_history": {}  # new addition for enhanced info scoring
}

def pick_seeded_word(seed_text):
    index = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % len(SOLUTIONS)
    return SOLUTIONS[index]

@app.route("/start_game")
def start_game():
    mode = request.args.get("mode", "infinity")
    state["mode"] = mode
    state["known_letters"] = set()
    state["known_positions"] = [None] * 5
    state["remaining_words"] = SOLUTIONS.copy()
    state["yellow_history"] = {}

    if mode == "daily":
        today = datetime.date.today().isoformat()
        state["secret"] = pick_seeded_word("daily" + today)
    elif mode == "hourly":
        hour = datetime.datetime.now().strftime("%Y-%m-%d %H")
        state["secret"] = pick_seeded_word("hourly" + hour)
    else:
        state["secret"] = random.choice(SOLUTIONS)

    return jsonify({
        "status": "ok",
        "mode": mode,
        "secretHash": hashlib.sha256(state["secret"].encode()).hexdigest()[:16]
    })

@app.route("/score", methods=["POST"])
def score_guess():
    data = request.get_json()
    guess = data.get("guess", "").lower()

    if guess not in ALL_VALID_GUESSES:
        return jsonify({
            "valid": False,
            "feedback": "",
            "elimination_score": 0,
            "info_score": 0,
            "correct": False,
            "secretHash": hashlib.sha256(state["secret"].encode()).hexdigest()[:16]
        })

    secret = state["secret"]
    feedback = list(give_feedback(secret, guess))

    # Elimination step
    starting_size = len(state["remaining_words"])
    filtered = []

    for word in state["remaining_words"]:
        word_feedback = list(give_feedback(word, guess))
        if word_feedback == feedback:
            filtered.append(word)

    remaining_size = len(filtered)
    state["remaining_words"] = filtered
    elimination_score = calculate_elimination_score(starting_size, remaining_size)

    # Improved information score using new scoring.py logic
    info_score = calculate_information_score(
        guess,
        feedback,
        state["known_letters"],
        state["known_positions"],
        state["yellow_history"]
    )

    return jsonify({
        "valid": True,
        "feedback": ''.join(feedback),
        "elimination_score": elimination_score,
        "info_score": info_score,
        "correct": guess == secret,
        "secretHash": hashlib.sha256(secret.encode()).hexdigest()[:16]
    })

@app.route("/secret")
def reveal_secret():
    return jsonify({"secret": state["secret"]})

# ✅ This is what starts Flask!
if __name__ == "__main__":
    app.run(debug=True)
