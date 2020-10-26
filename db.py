import sqlite3
from config import DB_PATH, LIMIT_DAYS, LIMIT_CHECK
import functools
import time

# only executes the function if leadless is false
def check(function):
	"""
	Doesn't let the decorated function execute if self.leadless is True.

	Returns if leadless is True, executes the function otherwise.
	"""

	@functools.wraps(function)
	def wrapper(self, *args, **kwargs):
		if getattr(self, "leadless"):
			return
		else:
			function(self, *args, **kwargs)
	return wrapper


class DB:
	"""
	Manages read/write intercations with the database.

	Attributes:
		Connection conn: The database connection.
		Cursor c = The database cursor.
		Boolean leadless: True if the instance should not write to the database, False otherwise.
		Float LIMIT_SECONDS: The threshold, in seconds, for reported_utc when fetching recent users.
	"""

	LIMIT_SECONDS = LIMIT_DAYS * 24 * 60 * 60
	LIMIT_CHECK_SECONDS = LIMIT_CHECK * 24 * 60 * 60

	def __init__(self, leadless):
		"""
		Initalizes a DB instance.

		Attributes:
			Connection conn: The database connection.
			Cursor c = The database cursor.
			Boolean leadless: True if the instance should not write to the database, False otherwise.
		"""

		self.conn = sqlite3.connect(DB_PATH)
		self.c = self.conn.cursor()
		self.leadless = leadless


	# Submissions
	@check
	def add_submission(self, post_id):
		"""
		Adds a submission to the database.

		Inserts a new entry to the SUBMISSIONS table with the given post_id and None/False for the other fields.

		Args:
			String post_id: The post_id value of the sql entry
		"""

		self.c.execute("INSERT INTO submissions VALUES(?, ?, ?, ?)", [post_id, None, None, False])
		self.conn.commit()


	@check
	def reject_submission(self, post_id, reason):
		"""

		Marks a submisison as rejected.

		Updates the entry in the SUBMISSIONS table with the given post id to be rejected with the given reason.

		Args:
			String post_id: The post_id of the submission to reject
			String reason: The reason the post was rejected
						   (one of REJECT_BLACKLISTED, REJECT_MALFORMATTED, REJECT_RESTRICTED, REJECT_REPORTED)
		"""

		self.c.execute("UPDATE submissions SET rejected=?, reason=? WHERE id=?", [True, reason, post_id])
		self.conn.commit()


	def restrict_submission(self, post_id):
		"""
		Marks a submission as restricted

		Updates the entry in the SUBMISSIONS table with the given post id to be restricted

		Args:
			String post_id: The post_id of the submission to mark restricted
		"""

		self.c.execute("UPDATE submissions SET restricted=? WHERE id=?", [True, post_id])
		self.conn.commit()




	def submission_exists(self, post_id):
		"""
		Checks if a submission exists

		Returns True if a submission exists in the SUBMISSIONS table with the given post_id, False otherwise

		Args:
			String post_id: the post_id to check for the existence of
		"""

		return True if self.c.execute("SELECT * FROM submissions WHERE id=?", [post_id]).fetchone() else False



	# Users
	@check
	def add_user(self, post_id, user_id, reported_utc, offense_type, blatant, reportee):
		"""
		Adds a user to the USERS table with the given information

		Args:
			String post_id: The post_id of the entry
			String user_id: The user_id of the entry
			String reported_utc: The unix timestamp the user was reported at
			String offense_type: What the user was reported for
			Boolean blatant: Whether the report called the cheats blatant or not
			String reportee: The reddit username of the reportee (not including the "u/")
		"""

		data = [post_id, user_id, reported_utc, None, offense_type, blatant, reportee]
		self.c.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?)", data)
		self.conn.commit()


	@check
	def restrict_user(self, post_id, time_utc):
		"""
		Restricts the user reported in the given post_id

		Updates the USERS table with the given post_id to have a restricted_utc of the passed time

		Args:
			String post_id: The post_id of the report to restrict
			String time_utc: The time the user was reported at
		"""

		self.c.execute("UPDATE users SET RESTRICTED_UTC=? WHERE post_id=?", [time_utc, post_id])
		self.conn.commit()


	def user_exists(self, user_id):
		"""
		Checks if a user exists.

		Checks if a user exists in the USERS table that was reported within the past LIMIT_SECONDS (equivelant to LIMIT_DAYS) seconds.

		Returns:
			The post_id of the entry if an entry meeting criteria was found,
			or None otherwise.
		"""

		result = self.c.execute("SELECT * FROM users WHERE user_id=? AND reported_utc > ?", [user_id, time.time() - DB.LIMIT_SECONDS]).fetchone()
		return result[0] if result else None


	def get_recent_users(self):
		"""
		Gets recently reported users.

		Retrives users that were reported within the past LIMIT_SECONDS seconds, and are not restricted yet.

		Returns:
			The values in the columns of the users table that meet the criteria.
		"""

		return self.c.execute("SELECT * FROM users WHERE reported_utc > ? AND restricted_utc IS NULL", [time.time() - DB.LIMIT_CHECK_SECONDS]).fetchall()


	# Misc
	def submissions_from_user(self, user_id):
		"""
		Returns the values in the columns of the users table where they have the given user_id
		"""

		return self.c.execute("SELECT * FROM users WHERE user_id=?", [user_id]).fetchall()
