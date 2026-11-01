#!/usr/bin/env python3
"""
Guess & Count
=============
Two small tools in one file:

1. A terminal number-guessing game with an attempt counter and a score.
2. A word-frequency tool that reads a text file and reports the most
   common words.

Scoring rule (guessing game)
----------------------------
* You get up to MAX_ATTEMPTS (10) valid guesses per round.
* A correct guess is worth 100 points on the 1st attempt, and 10 fewer
  points for every extra attempt (100, 90, 80 ... 10).
* Running out of attempts scores 0 for that round.
* Invalid input (letters, or a number outside 1-100) does NOT use up an
  attempt.
* Round scores are added to a running session total.

Run with:  python guess_and_count.py
"""

import random  # imported once, at the top

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
LOW, HIGH = 1, 100
MAX_ATTEMPTS = 10
START_POINTS = 100
PENALTY_PER_EXTRA_ATTEMPT = 10

# Very common English words that usually dominate a frequency report.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on",
    "at", "by", "for", "with", "from", "as", "is", "are", "was", "were",
    "be", "been", "it", "its", "this", "that", "these", "those", "i",
    "you", "he", "she", "we", "they", "them", "his", "her", "my", "your",
    "our", "their", "not", "no", "so", "do", "did", "has", "have", "had",
}


# ----------------------------------------------------------------------
# Part 1: Guessing game
# ----------------------------------------------------------------------
def calculate_score(attempts_used):
    """Return the points earned for winning on the given attempt number."""
    return max(0, START_POINTS - PENALTY_PER_EXTRA_ATTEMPT * (attempts_used - 1))


def play_round():
    """Play one round. Returns the points earned (0 if the player loses)."""
    secret = random.randint(LOW, HIGH)  # picked ONCE per round, not per guess
    attempts = 0

    print(f"\nI'm thinking of a number between {LOW} and {HIGH}.")
    print(f"You have {MAX_ATTEMPTS} attempts. Good luck!\n")

    while attempts < MAX_ATTEMPTS:
        raw = input(f"Attempt {attempts + 1}/{MAX_ATTEMPTS} - your guess: ").strip()

        try:
            guess = int(raw)
        except ValueError:
            print("  Please enter a whole number.")
            continue  # does not use up an attempt

        if not LOW <= guess <= HIGH:
            print(f"  Please stay between {LOW} and {HIGH}.")
            continue  # does not use up an attempt

        attempts += 1

        if guess == secret:
            points = calculate_score(attempts)
            word = "attempt" if attempts == 1 else "attempts"
            print(f"  Correct! You got it in {attempts} {word}.")
            print(f"  Round score: {points}")
            return points

        print("  Too low." if guess < secret else "  Too high.")

    print(f"\n  Out of attempts! The number was {secret}. Round score: 0")
    return 0


def run_game():
    """Play rounds until the player stops; show the session summary."""
    total = 0
    rounds = 0
    best = 0

    while True:
        points = play_round()
        rounds += 1
        total += points
        best = max(best, points)
        print(f"  Session total: {total}  |  Best round: {best}  |  Rounds: {rounds}")

        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            break

    print(f"\nFinal session score: {total} over {rounds} round(s).")


# ----------------------------------------------------------------------
# Part 2: Word-frequency tool
# ----------------------------------------------------------------------
def read_text_file(path):
    """Read a whole text file safely. Returns the text, or None on error."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        print(f"  Error: file '{path}' was not found.")
    except IsADirectoryError:
        print(f"  Error: '{path}' is a folder, not a file.")
    except PermissionError:
        print(f"  Error: no permission to read '{path}'.")
    except OSError as err:
        print(f"  Error: could not read '{path}' ({err}).")
    return None


def tokenize(text):
    """Split text into lowercase words (letters, with inner apostrophes)."""
    words = []
    current = []
    for ch in text.lower():
        if ch.isalpha() or (ch == "'" and current):
            current.append(ch)
        else:
            if current:
                words.append("".join(current).strip("'"))
                current = []
    if current:
        words.append("".join(current).strip("'"))
    return [w for w in words if w]


def count_words(words, ignore_common=False):
    """Count words using a dictionary: {word: count}."""
    counts = {}
    for word in words:
        if ignore_common and word in STOP_WORDS:
            continue
        counts[word] = counts.get(word, 0) + 1
    return counts


def top_words(counts, n):
    """Sort by frequency (high to low); ties are broken alphabetically."""
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]


def print_report(path, ignore_common, n):
    text = read_text_file(path)
    if text is None:
        return

    words = tokenize(text)
    if not words:
        print("  The file is empty or contains no words.")
        return

    counts = count_words(words, ignore_common)
    if not counts:
        print("  Every word in the file was a common word that was filtered out.")
        return

    ranked = top_words(counts, n)
    biggest = ranked[0][1]

    print(f"\n  File: {path}")
    print(f"  Total words: {len(words)}  |  Unique words: {len(counts)}")
    if ignore_common:
        print("  (common words like 'the' and 'and' are hidden)")
    print(f"\n  Top {len(ranked)} words:")
    print(f"  {'#':>3}  {'word':<15}{'count':>6}")
    print("  " + "-" * 40)
    for rank, (word, count) in enumerate(ranked, start=1):
        bar = "#" * max(1, round(20 * count / biggest))
        print(f"  {rank:>3}  {word:<15}{count:>6}  {bar}")


def run_word_counter():
    path = input("\nPath to a text file: ").strip().strip('"').strip("'")
    if not path:
        print("  No file name entered.")
        return

    raw_n = input("How many top words to show? [10]: ").strip()
    n = 10
    if raw_n:
        if raw_n.isdigit() and int(raw_n) > 0:
            n = int(raw_n)
        else:
            print("  Not a positive number, using 10.")

    hide = input("Hide common words like 'the' and 'and'? (y/n) [n]: ").strip().lower()
    print_report(path, ignore_common=(hide == "y"), n=n)


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
def main():
    print("=" * 40)
    print("        GUESS & COUNT")
    print("=" * 40)

    while True:
        print("\n1) Play the guessing game")
        print("2) Count words in a text file")
        print("3) Quit")
        choice = input("Choose 1-3: ").strip()

        if choice == "1":
            run_game()
        elif choice == "2":
            run_word_counter()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("  Please type 1, 2 or 3.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")