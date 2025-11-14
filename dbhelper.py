import sqlite3

DB_NAME = "election.db"

# ---------------------------------------------------
# CONNECT FUNCTION (used by all other functions)
# ---------------------------------------------------
def get_connection():
    # enable row access by name if you want: sqlite3.Row
    conn = sqlite3.connect(DB_NAME)
    return conn


# ---------------------------------------------------
# INITIAL DATABASE SETUP (RUNS AUTOMATICALLY ON IMPORT)
# includes migration to add voterActive column if missing
# ---------------------------------------------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # POSITIONS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            posID INTEGER PRIMARY KEY AUTOINCREMENT,
            posName TEXT NOT NULL,
            numOfPositions INTEGER NOT NULL,
            posStat TEXT NOT NULL DEFAULT 'open'
        );
    """)

    # VOTERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            voterID INTEGER PRIMARY KEY AUTOINCREMENT,
            voterPass TEXT NOT NULL,
            voterFName TEXT NOT NULL,
            voterMName TEXT,
            voterLName TEXT NOT NULL,
            voterStat TEXT NOT NULL DEFAULT 'active',
            voted TEXT NOT NULL DEFAULT 'n'
        );
    """)

    # CANDIDATES TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            candID INTEGER PRIMARY KEY AUTOINCREMENT,
            candFName TEXT NOT NULL,
            candMName TEXT,
            candLName TEXT NOT NULL,
            posID INTEGER NOT NULL,
            candStat TEXT NOT NULL DEFAULT 'active',
            votes INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (posID) REFERENCES positions(posID)
        );
    """)

    # VOTES TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            posID INTEGER NOT NULL,
            voterID INTEGER NOT NULL,
            candID INTEGER NOT NULL,
            FOREIGN KEY (posID) REFERENCES positions(posID),
            FOREIGN KEY (voterID) REFERENCES voters(voterID),
            FOREIGN KEY (candID) REFERENCES candidates(candID)
        );
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------
# CRUD FUNCTIONS (Positions)
# ---------------------------------------------------
def add_position(name, num_of_positions, stat):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO positions (posName, numOfPositions, posStat) VALUES (?, ?, ?)",
                (name, num_of_positions, stat))
    conn.commit()
    conn.close()


def update_position(pid, name=None, num_of_positions=None, stat=None):
    conn = get_connection()
    cur = conn.cursor()
    # Fetch current values
    cur.execute("SELECT posName, numOfPositions, posStat FROM positions WHERE posID=?", (pid,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    current_name, current_num, current_stat = row
    # Use current values if None is passed
    name = name if name is not None else current_name
    num_of_positions = num_of_positions if num_of_positions is not None else current_num
    stat = stat if stat is not None else current_stat
    cur.execute("""
        UPDATE positions SET posName=?, numOfPositions=?, posStat=? WHERE posID=?
    """, (name, num_of_positions, stat, pid))
    conn.commit()
    conn.close()


# ---------------------------------------------------
# CRUD FUNCTIONS (Candidates)
# ---------------------------------------------------
def add_candidate(fname, mname, lname, position_id, stat='active'):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO candidates (candFName, candMName, candLName, posID, candStat) VALUES (?, ?, ?, ?, ?)",
                (fname, mname, lname, position_id, stat))
    conn.commit()
    conn.close()


def update_candidate(cid, fname, mname, lname, position_id, stat):
    conn = get_connection()
    cur = conn.cursor()
    # Fetch current values if any argument is None
    cur.execute("SELECT candFName, candMName, candLName, posID, candStat FROM candidates WHERE candID=?", (cid,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    current_fname, current_mname, current_lname, current_posid, current_stat = row
    fname = fname if fname is not None else current_fname
    mname = mname if mname is not None else current_mname
    lname = lname if lname is not None else current_lname
    position_id = position_id if position_id is not None else current_posid
    stat = stat if stat is not None else current_stat
    cur.execute("""
        UPDATE candidates SET candFName=?, candMName=?, candLName=?, posID=?, candStat=? WHERE candID=?
    """, (fname, mname, lname, position_id, stat, cid))
    conn.commit()
    conn.close()


# ---------------------------------------------------
# CRUD FUNCTIONS (Voters)
# ---------------------------------------------------
def add_voter(password, fname, mname, lname, stat='active', voted='n'):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO voters (voterPass, voterFName, voterMName, voterLName, voterStat, voted) VALUES (?, ?, ?, ?, ?, ?)",
                (password, fname, mname, lname, stat, voted))
    conn.commit()
    conn.close()


def update_voter(vid, password, fname, mname, lname, stat):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE voters SET voterPass=?, voterFName=?, voterMName=?, voterLName=?, voterStat=? WHERE voterID=?
    """, (password, fname, mname, lname, stat, vid))
    conn.commit()
    conn.close()


# ---------------------------------------------------
# LOGIN FUNCTION (now checks active + voted)
# returns a tuple (voterID, voterStat, voterActive) or None
# ---------------------------------------------------
def validate_voter_login(voter_id, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT voterID, voterStat, voted FROM voters WHERE voterID=? AND voterPass=?",
                (voter_id, password))
    result = cur.fetchone()
    conn.close()
    return result  # None or (voterID, voterStat, voted)


# ---------------------------------------------------
# VOTING FUNCTION
# ---------------------------------------------------
def cast_vote(position_id, voter_id, candidate_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO votes (posID, voterID, candID) VALUES (?, ?, ?)",
                (position_id, voter_id, candidate_id))
    cur.execute("UPDATE candidates SET votes = votes + 1 WHERE candID=?", (candidate_id,))
    conn.commit()
    conn.close()


def mark_voter_as_voted(voter_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE voters SET voted='y' WHERE voterID=?", (voter_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------
# RESULTS FUNCTIONS
# ---------------------------------------------------
def get_results():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT candidates.candFName || ' ' || candidates.candLName AS candName, positions.posName, candidates.votes
        FROM candidates
        JOIN positions ON candidates.posID = positions.posID
        ORDER BY positions.posID, candidates.votes DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_results_with_percent():
    conn = get_connection()
    cur = conn.cursor()
    # Get total votes per position
    cur.execute("""
        SELECT posID, SUM(votes) as total_votes
        FROM candidates
        GROUP BY posID
    """)
    totals = {row[0]: row[1] for row in cur.fetchall()}
    # Get candidate results
    cur.execute("""
        SELECT candidates.candFName || ' ' || candidates.candLName AS candName,
               positions.posName,
               candidates.votes,
               candidates.posID
        FROM candidates
        JOIN positions ON candidates.posID = positions.posID
        ORDER BY positions.posID, candidates.votes DESC
    """)
    rows = cur.fetchall()
    results = []
    for candName, posName, votes, posID in rows:
        total = totals.get(posID, 0)
        percent = (votes / total * 100) if total > 0 else 0
        results.append((candName, posName, votes, f"{percent:.2f}"))
    conn.close()
    return results


# ---------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------
def get_voter_info(voter_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT voterID, voterStat, voted FROM voters WHERE voterID=?", (voter_id,))
    result = cur.fetchone()
    conn.close()
    return result  # (voterID, voterStat, voted)

def get_num_of_positions(pos_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT numOfPositions FROM positions WHERE posID=?", (pos_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 1

def get_position_name(pos_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT posName FROM positions WHERE posID=?", (pos_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else ""

# Run database initializer on import
init_db()
