from flask import Flask, render_template, request, redirect
import dbhelper

app = Flask(__name__, static_folder='statics')

# HOME
@app.route("/")
def home():
    return render_template("index.html")

# POSITIONS
@app.route("/positions")
def positions():
    conn = dbhelper.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM positions")
    data = cur.fetchall()
    conn.close()
    return render_template("positions.html", positions=data)


@app.route("/positions/add", methods=["POST"])
def add_position():
    name = request.form["name"]
    num_of_positions = request.form["num_of_positions"]
    stat = request.form["stat"]
    dbhelper.add_position(name, num_of_positions, stat)
    return redirect("/positions")


@app.route("/positions/update", methods=["POST"])
def update_position():
    pid = request.form["pid"]
    name = request.form["name"]
    num_of_positions = request.form["num_of_positions"]
    stat = request.form["stat"]
    dbhelper.update_position(pid, name, num_of_positions, stat)
    return redirect("/positions")


# CANDIDATES
@app.route("/candidates")
def candidates():
    conn = dbhelper.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.candID, c.candFName, c.candMName, c.candLName, p.posName, c.candStat
        FROM candidates c
        JOIN positions p ON c.posID = p.posID
    """)
    data = cur.fetchall()

    cur.execute("SELECT posID, posName FROM positions WHERE posStat='open'")
    positions = cur.fetchall()
    conn.close()
    return render_template("candidates.html", candidates=data, positions=positions)


@app.route("/candidates/add", methods=["POST"])
def add_candidate():
    fname = request.form["fname"]
    mname = request.form.get("mname", "")
    lname = request.form["lname"]
    pos = request.form["pos"]
    stat = request.form["stat"]
    dbhelper.add_candidate(fname, mname, lname, pos, stat)
    return redirect("/candidates")


@app.route("/candidates/update", methods=["POST"])
def update_candidate():
    cid = request.form["cid"]
    fname = request.form["fname"]
    mname = request.form.get("mname", "")
    lname = request.form["lname"]
    pos = request.form["pos"]
    stat = request.form["stat"]
    dbhelper.update_candidate(cid, fname, mname, lname, pos, stat)
    return redirect("/candidates")


@app.route("/candidates/deactivate", methods=["POST"])
def candidates_deactivate():
    cid = request.form.get("cid")
    if cid:

        dbhelper.update_candidate(cid, None, None, None, None, "inactive")
    return redirect("/candidates")


@app.route("/candidates/activate", methods=["POST"])
def candidates_activate():
    cid = request.form.get("cid")
    if cid:
        dbhelper.update_candidate(cid, None, None, None, None, "active")
    return redirect("/candidates")

# VOTERS
@app.route("/voters")
def voters():
    conn = dbhelper.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM voters")
    data = cur.fetchall()
    conn.close()
    return render_template("voters.html", voters=data)


@app.route("/voters/add", methods=["POST"])
def add_voter():
    password = request.form["password"]
    fname = request.form["fname"]
    mname = request.form.get("mname", "")
    lname = request.form["lname"]
    stat = request.form.get("stat", "active")
    dbhelper.add_voter(password, fname, mname, lname, stat)
    return redirect("/voters")


@app.route("/voters/update", methods=["POST"])
def update_voter():
    vid = request.form["vid"]
    password = request.form["password"]
    fname = request.form["fname"]
    mname = request.form.get("mname", "")
    lname = request.form["lname"]
    stat = request.form.get("stat", "active")
    dbhelper.update_voter(vid, password, fname, mname, lname, stat)
    return redirect("/voters")


@app.route("/voters/deactivate", methods=["POST"])
def voters_deactivate():
    vid = request.form.get("vid")
    if vid:
        dbhelper.update_voter(vid, None, None, None, None, "inactive")
    return redirect("/voters")


@app.route("/voters/activate", methods=["POST"])
def voters_activate():
    vid = request.form.get("vid")
    if vid:
        dbhelper.update_voter(vid, None, None, None, None, "active")
    return redirect("/voters")


# VOTING
@app.route("/vote/login", methods=["GET", "POST"])
def vote_login():
    if request.method == "GET":
        return render_template("vote_login.html")

    voterID = request.form["voterID"]
    password = request.form["password"]

    result = dbhelper.validate_voter_login(voterID, password)

    if result is None:
        return "Invalid login"

    voter_id, voter_stat, voted = result
    if voter_stat != "active":
        return "Your account is inactive. Please contact administrator."

    if voted == "y":
        return "You already voted."

    return redirect(f"/vote/{voterID}")


@app.route("/vote/<voter_id>")
def vote_page(voter_id):
    conn = dbhelper.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT posID, posName, numOfPositions FROM positions WHERE posStat='open'")
    positions = cur.fetchall()
    cur.execute("""
        SELECT c.candID, c.candFName || ' ' || c.candMName || ' ' || c.candLName, c.posID
        FROM candidates c
        JOIN positions p ON c.posID = p.posID
        WHERE c.candStat='active' AND p.posStat='open'
    """)
    candidates = cur.fetchall()
    conn.close()
    pos_dict = {}
    for pos in positions:
        pos_id, pos_name, num_of_positions = pos
        pos_dict[pos_id] = {
            'name': pos_name,
            'num': num_of_positions,
            'candidates': []
        }
    for cand in candidates:
        cand_id, cand_name, pos_id = cand
        if pos_id in pos_dict:
            pos_dict[pos_id]['candidates'].append((cand_id, cand_name))
    return render_template("vote.html", voter_id=voter_id, positions=pos_dict)


@app.route("/vote/submit", methods=["POST"])
def submit_vote():
    voter_id = request.form["voter_id"]

    voter_info = dbhelper.get_voter_info(voter_id)
    if not voter_info or voter_info[1] != "active":
        return "Your account is inactive. Please contact administrator."
    if voter_info[2] == "y":
        return "You already voted."

    votes = []
    for key in request.form:
        if key.startswith("pos_"):
            pos_id = key.split("_")[1]
            cand_ids = request.form.getlist(key)

            num_allowed = dbhelper.get_num_of_positions(pos_id)
            if len(cand_ids) > num_allowed:
                return f"Too many votes for position {dbhelper.get_position_name(pos_id)} (max {num_allowed})"
            for cand_id in cand_ids:
                votes.append((pos_id, voter_id, cand_id))

    for pos_id, voter_id, cand_id in votes:
        dbhelper.cast_vote(pos_id, voter_id, cand_id)
    dbhelper.mark_voter_as_voted(voter_id)
    return "Vote submitted successfully!"


# RESULTS
@app.route("/results")
def results():
    rows = dbhelper.get_results_with_percent()
    return render_template("results.html", results=rows)


# WINNERS
@app.route("/winners")
def winners():
    conn = dbhelper.get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.posName, c.candFName || ' ' || c.candMName || ' ' || c.candLName, MAX(c.votes)
        FROM candidates c
        JOIN positions p ON c.posID = p.posID
        GROUP BY c.posID
        ORDER BY MAX(c.votes) DESC
    """)

    data = cur.fetchall()
    conn.close()

    return render_template("winners.html", winners=data)


@app.route("/positions/deactivate", methods=["POST"])
def positions_deactivate():
    pid = request.form.get("pid")
    if pid:
        dbhelper.update_position(pid, None, None, "closed")
    return redirect("/positions")


@app.route("/positions/activate", methods=["POST"])
def positions_activate():
    pid = request.form.get("pid")
    if pid:
        dbhelper.update_position(pid, None, None, "open")
    return redirect("/positions")


if __name__ == "__main__":
    app.run(debug=True)
