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


@app.route("/positions/delete", methods=["POST"])
def positions_delete():
    pid = request.form.get("pid")
    if pid:
        dbhelper.delete_position(pid)
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


@app.route("/candidates/delete", methods=["POST"])
def candidates_delete():
    cid = request.form.get("cid")
    if cid:
        dbhelper.delete_candidate(cid)
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


@app.route("/voters/delete", methods=["POST"])
def voters_delete():
    vid = request.form.get("vid")
    if vid:
        dbhelper.delete_voter(vid)
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
    info = dbhelper.get_voter_info(voter_id)
    if not info or info[1] != "active" or info[2] == "y": return "Your account is inactive or already voted."
    for k in request.form: 
        if k.startswith("pos_"):
            ids = request.form.getlist(k)
            if len(ids) > dbhelper.get_num_of_positions(k.split("_")[1]): return "Too many votes."
            for cid in ids: dbhelper.cast_vote(k.split("_")[1], voter_id, cid)
    dbhelper.mark_voter_as_voted(voter_id)
    return "Vote submitted successfully!"


# RESULTS
@app.route("/results")
def results():
    return render_template("results.html", results=dbhelper.get_results_with_percent())


# WINNERS
@app.route("/winners")
def winners():
    conn = dbhelper.get_connection()
    data = conn.execute("""
        SELECT p.posName, c.candFName || ' ' || c.candMName || ' ' || c.candLName, MAX(c.votes)
        FROM candidates c JOIN positions p ON c.posID = p.posID GROUP BY c.posID ORDER BY MAX(c.votes) DESC
    """).fetchall()
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
