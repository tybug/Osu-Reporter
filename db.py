import sqlite3
from config import DB


# Submissions

def add_submission(id):
	c = sqlite3.connect(DB)
	c.execute("INSERT INTO posts VALUES(?)", [id])
	c.commit()
	c.close()


def submission_exists(id):
	c = sqlite3.connect(DB)
	try:
		for row in c.execute("SELECT * FROM posts WHERE id=?", [id]):
			return True
		return False
	finally:
		c.close()



# Users

def add_user(id, post, date, offense_type, blatant, reportee):
	c = sqlite3.connect(DB)
	data = [id, post, date, offense_type, blatant, reportee]
	c.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?)", data)
	c.commit()
	c.close()


def remove_user(id):
	c = sqlite3.connect(DB)
	c.execute("DELETE FROM users WHERE id=?", [id])
	c.commit()
	c.close()



def user_exists(id):
	c = sqlite3.connect(DB)
	try:
		for row in c.execute("SELECT * FROM users WHERE id=?", [id]):
			return True
		return False
	finally:
		c.close()

def get_all_users():
	c = sqlite3.connect(DB)
	users = []
	for row in c.execute("SELECT * FROM users"):
		users.append(row)

	return users


# Misc

def post_from_user(id):
	c = sqlite3.connect(DB)
	try:
		cursor = c.cursor()
		cursor.execute("SELECT * FROM users WHERE id=?", [id])
		for row in cursor:
			return row[1] # row["post"]
	finally:
		c.close()


# Stats
def add_stat(user, post, reported_utc, restricted_utc, offense_type, blatant, reportee):
	c = sqlite3.connect(DB)
	data = [user, post, reported_utc, restricted_utc, offense_type, blatant, reportee]
	c.execute("INSERT INTO stats VALUES(?, ?, ?, ?, ?, ?, ?)", data)
	c.commit()
	c.close()