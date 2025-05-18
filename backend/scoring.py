# backend/scoring.py

SECRET_WORD = "crane"  # For now — you can make this dynamic later

def give_feedback(secret, guess):
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

    return ''.join(feedback)

def calculate_elimination_score(starting_pool_size=1000, remaining_pool_size=100):
    if starting_pool_size == 0:
        return 0
    eliminated = starting_pool_size - remaining_pool_size
    score = (eliminated / starting_pool_size) * 100
    return round(score)

def calculate_information_score(guess, feedback, known_letters, known_positions, yellow_history):
    new_info = 0
    for idx, (g_letter, fb) in enumerate(zip(guess, feedback)):
        if fb == 'G' and known_positions[idx] is None:
            known_positions[idx] = g_letter
            new_info += 1

        elif fb == 'Y':
            history = yellow_history.setdefault(g_letter, set())
            if idx not in history:
                history.add(idx)
                new_info += 0.5  # Partial credit for learning new wrong position
            if g_letter not in known_letters:
                known_letters.add(g_letter)
                new_info += 0.5  # Partial credit for confirming presence

        elif fb == '_' and g_letter not in known_letters:
            known_letters.add(g_letter)
            new_info += 0.25  # Small credit for elimination

    return int(min(new_info * 20, 100))  # Scale up to max 100
