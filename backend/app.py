from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import datetime
import hashlib

print("✅ Flask is loading app.py...")  # Debug line

app = Flask(__name__)
CORS(app)

# Load curated solution words (used for secret word)
with open("backend/solution_words.txt") as f:
    SOLUTIONS = [w.strip().lower() for w in f if len(w.strip()) == 5]

# Load large list of accepted guesses
with open("backend/allowed_guesses.txt") as f:
    ALLOWED_GUESSES = set(w.strip().lower() for w in f if len(w.strip()) == 5)

# Union of both is the full valid guess set
ALL_VALID_GUESSES = set(SOLUTIONS) | ALLOWED_GUESSES

state = {
    "mode": "infinity",
    "secret": random.choice(SOLUTIONS),
    "remaining_words": SOLUTIONS.copy(),
    "known_letters": set(),
    "known_positions": [None] * 5
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
    feedback = ['_' for _ in range(len(secret))]
    secret_letters = list(secret)

    for i in range(len(secret)):
        if guess[i] == secret[i]:
            feedback[i] = 'G'
            secret_letters[i] = None

    for i in range(len(secret)):
        if feedback[i] == '_' and guess[i] in secret_letters:
            feedback[i] = 'Y'
            secret_letters[secret_letters.index(guess[i])] = None

    # Calculate elimination score
    starting_size = len(state["remaining_words"])
    filtered = []
    for word in state["remaining_words"]:
        temp_fb = ['_' for _ in range(len(secret))]
        temp_letters = list(word)

        for i in range(len(secret)):
            if guess[i] == word[i]:
                temp_fb[i] = 'G'
                temp_letters[i] = None

        for i in range(len(secret)):
            if temp_fb[i] == '_' and guess[i] in temp_letters:
                temp_fb[i] = 'Y'
                temp_letters[temp_letters.index(guess[i])] = None

        if temp_fb == feedback:
            filtered.append(word)

    remaining_size = len(filtered)
    state["remaining_words"] = filtered

    eliminated = starting_size - remaining_size
    elimination_score = round((eliminated / starting_size) * 100) if starting_size > 0 else 0

    # Calculate information score
    new_info = 0
    for idx, (g_letter, fb) in enumerate(zip(guess, feedback)):
        if fb == 'G' and state["known_positions"][idx] is None:
            new_info += 1
            state["known_positions"][idx] = g_letter
        elif fb == 'Y' and g_letter not in state["known_letters"]:
            new_info += 1
            state["known_letters"].add(g_letter)
        elif fb == '_' and g_letter not in state["known_letters"]:
            new_info += 0.5
            state["known_letters"].add(g_letter)

    info_score = int(min(new_info * 20, 100))  # Scale up to max 100

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
