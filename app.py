
from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import hashlib
from datetime import date

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "demo-secret-change-this")

CANDIDATES = ["Deepika", "Varun", "Shreya","Chiranth"]
VOTES_FILE = "votes.json"
VOTERS_FILE = "voters.json"


def read_json(filename, default):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else default.copy()
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default.copy()


def load_votes():
    saved = read_json(VOTES_FILE, {})
    return {name: saved.get(name, 0) for name in CANDIDATES}


def save_votes(votes):
    with open(VOTES_FILE, "w") as file:
        json.dump(votes, file, indent=4)


def voter_key(name, dob):
    value = name.strip().casefold() + "|" + dob
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        session.pop("voter_key", None)
        return render_template("register.html", message="")

    name = request.form.get("name", "").strip()
    dob = request.form.get("dob", "")

    if not name or not dob:
        return render_template(
            "register.html", message="Please enter your name and DOB."
        )

    try:
        birth_date = date.fromisoformat(dob)
        if birth_date >= date.today():
            raise ValueError
    except ValueError:
        return render_template(
            "register.html", message="Please enter a valid date of birth."
        )

    identity = voter_key(name, dob)
    voters = read_json(VOTERS_FILE, {})

    if identity in voters:
        return render_template(
            "register.html",
            message="This name and DOB have already voted. A second vote is not allowed."
        )

    session["voter_key"] = identity
    session["voter_name"] = name

    return redirect(url_for("voting"))


@app.route("/voting", methods=["GET", "POST"])
def voting():
    identity = session.get("voter_key")

    if not identity:
        return redirect(url_for("register"))

    voters = read_json(VOTERS_FILE, {})

    if identity in voters:
        session.clear()
        return redirect(url_for("register"))

    message = ""

    if request.method == "POST":
        candidate = request.form.get("candidate")

        if candidate not in CANDIDATES:
            message = "Please select a valid candidate."
        else:
            # Recheck before recording the vote.
            voters = read_json(VOTERS_FILE, {})
            if identity in voters:
                session.clear()
                return redirect(url_for("register"))

            votes = load_votes()
            votes[candidate] += 1
            voters[identity] = True

            save_votes(votes)
            with open(VOTERS_FILE, "w") as file:
                json.dump(voters, file, indent=4)

            session.clear()
            return render_template(
                "vote.html",
                candidates=CANDIDATES,
                votes=load_votes(),
                total_votes=sum(load_votes().values()),
                message="Thank you! Your vote has been recorded.",
                completed=True
            )

    votes = load_votes()
    return render_template(
        "vote.html",
        candidates=CANDIDATES,
        votes=votes,
        total_votes=sum(votes.values()),
        message=message,
        completed=False
    )


@app.route("/restart", methods=["POST"])
def restart():
    # Demo only: this clears every vote and voter record.
    save_votes({name: 0 for name in CANDIDATES})
    with open(VOTERS_FILE, "w") as file:
        json.dump({}, file)
    session.clear()
    return redirect(url_for("register"))


if __name__ == "__main__":
    app.run(debug=True)

