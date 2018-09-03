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

def add_user(id, post, date):
	c = sqlite3.connect(DB)
	data = [id, post, date]
	c.execute("INSERT INTO users VALUES(?, ?, ?)", data)
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
	ret = []
	for row in c.execute("SELECT * FROM users"):
		ret.append(row)

	return ret

