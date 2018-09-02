import sqlite3
from config import DB



def add_submission(id):
	c = sqlite3.connect(DB)
	c.execute("INSERT INTO posts VALUES(?)", [id])
	c.commit()
	c.close()


def add_user(id, post):
	c = sqlite3.connect(DB)
	data = [id, post]
	c.execute("INSERT INTO users VALUES(?, ?)", data)
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


def get_all_users():
	c = sqlite3.connect(DB)
	ret = []
	for row in c.execute("SELECT * FROM users"):
		ret.append(row)

	return ret


def remove_user(id):
	c = sqlite3.connect(DB)
	c.execute("DELETE FROM users WHERE id=?", id)
	c.commit()
	c.close()