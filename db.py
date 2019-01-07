import sqlite3
from config import DB_PATH, LIMIT_DAYS
import functools
import time

# only executes the function if leadless is false
def check(function):
	@functools.wraps(function)
	def wrapper(self, *args, **kwargs):
		if(getattr(self, "leadless")):
			return
		else:
			function(self, *args, **kwargs)
	return wrapper



# leadless = can't write to db
class DB:

	def __init__(self, leadless):
		self.conn = sqlite3.connect(DB_PATH)
		self.c = self.conn.cursor()
		self.leadless = leadless
		self.LIMIT_SECONDS = time.time() - LIMIT_DAYS * 24 * 60 * 60

	
	# Submissions
	@check
	def add_submission(self, post_id):
		self.c.execute("INSERT INTO submissions VALUES(?, ?, ?, ?)", [post_id, None, None, False])
		self.conn.commit()


	@check
	def reject_submission(self, post_id, rejected, reason):
		'''
		Updates the submission with the given post id to be rejected with the given reason

		table: submissions
		'''
		self.c.execute("UPDATE submissions SET rejected=?, reason=? WHERE id=?", [rejected, reason, post_id])
		self.conn.commit()


	def restrict_submission(self, post_id):
		'''
		Updates the submission with the given post id to be restricted

		table: submissions
		'''
		self.c.execute("UPDATE submissions SET restricted=? WHERE id=?", [True, post_id])
		self.conn.commit()
		



	def submission_exists(self, post_id):
		return True if self.c.execute("SELECT * FROM submissions WHERE id=?", [post_id]).fetchone() else False



	# Users
	@check
	def add_user(self, post_id, user_id, reported_utc, offense_type, blatant, reportee):
		data = [post_id, user_id, reported_utc, None, offense_type, blatant, reportee]
		self.c.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?)", data)
		self.conn.commit()


	@check
	def restrict_user(self, post_id, time_utc):
		self.c.execute("UPDATE users SET RESTRICTED_UTC=? WHERE post_id=?", [time_utc, post_id])
		self.conn.commit()


	def user_exists(self, user_id):
		'''
		Returns the post id if there is an entry in the users table with the given id, and a date more recent than LIMIT_DAYS ago.
		Otherwise returns None
		'''
		result = self.c.execute("SELECT * FROM users WHERE user_id=? AND reported_utc > ?", [user_id, self.LIMIT_SECONDS]).fetchone()
		return result[1] if result else None
		

	def get_recent_users(self):
		return self.c.execute("SELECT * FROM users WHERE reported_utc > ? AND restricted_utc IS NULL", [self.LIMIT_SECONDS]).fetchall()


	# Misc
	def submissions_from_user(self, user_id):
		return self.c.execute("SELECT * FROM users WHERE user_id=?", [user_id]).fetchall()

