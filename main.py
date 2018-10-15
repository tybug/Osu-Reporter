import praw
from config import *
import secret
import re
from parser import *
from db import *
import threading
import datetime

# keep reddit global
reddit = praw.Reddit(client_id=secret.ID,
                     client_secret=secret.SECRET,
                     user_agent="python:com.tybug.osureporter:v" + secret.VERSION + " (by /u/tybug2)",
                     username=secret.USERNAME,
                     password=secret.PASSWORD)

def main():

	subreddit = reddit.subreddit(SUB)
	check_banned() # automatically repeats on interval

	# Iterate over every new submission
	for submission in subreddit.stream.submissions():
		process_submission(submission)


def process_submission(submission):
	if(submission_exists(submission.id)): # Already processed; praw returns the past 100 results for streams, previously iterated over or not
		return
	print("Processing submission https://old.reddit.com{}".format(submission.permalink))
	add_submission(submission.id)


	title = submission.title
	for strip in TITLE_STRIP:
		# Escape for regex
		if(strip in ESCAPE_REQUIRED):
			strip = "\\" + strip
		title = re.sub(strip, "", title)


	title_data = re.split(TITLE_SPLIT, title)
	if(len(title_data) < 3): 
		if(REPLY_MALFORMAT_COMMENT):
			# submission.reply(REPLY_MALFORMAT_COMMENT + REPLY_INFO)
			pass
		return


	gamemode = parse_gamemode(title_data[0])
	player = title_data[1]
	offense = title_data[2]

	# Flair it
	flair_data = parse_flair_data(offense)
	if(flair_data):
		if(submission.link_flair_text == "Resolved"): # don't overwrite resolved flairs
			print("I would have flaired {} as {}, but it was already resolved".format(submission.permalink, flair_data[0]))
		else:
			submission.mod.flair(flair_data[0], flair_data[1])


	if([i for i in title_data if i in REPLY_IGNORE]): # if the title has any blacklisted words (for discssion threads), don't process it further
		print("Would have processed {} further, but it contained blacklisted words".format(submission.permalink))
		return
	
	player_data = parse_user_data(player, gamemode, "string")
	if(player_data is None): # api gives empty json - possible misspelling or user was already banned
		if(REPLY_ALREADY_BANNED):
			# submission.reply(REPLY_ALREADY_BANNED.format(USERS + player) + REPLY_INFO)
		return

	# submission.reply(create_reply(player_data))

	# only add to db if it's not already there
	if(not user_exists(player_data[0]["user_id"])):
		add_user(player_data[0]["user_id"], submission.id, submission.created_utc)



def check_banned():
	threading.Timer(CHECK_INTERVAL, check_banned).start() # Calls this function after x seconds, which calls itself. Cheap way to check for banned users on an interval

	for data in get_all_users():

		id = data[0] # user id
		post_id = data[1] # post id
		post_date = data[2] # post submission date

		post_date = int(float(post_date))
		difference = datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(post_date)
		if(difference.total_seconds() > LIMIT_DAYS * 24 * 60 * 60): # compare seconds
			remove_user(id)
			return


		user_data = parse_user_data(id, "0", "id") # gamemode doesn't matter here since we're just checking for empty response

		if(user_data is None): # user was restricted
			remove_user(id)
			post = praw.Submission(reddit, post_id) # get praw post from id to flair
			print("Flairing {} as resolved".format(post.permalink))
			post.mod.flair("Resolved", "resolved")


	# Might as well forward pms here...already have an automated function, why not?
	for message in reddit.inbox.unread():		
		reddit.redditor(AUTHOR).message("REPLY to Report Bot FROM u/{}".format(message.author), message.body)
		message.mark_read()


if __name__ == "__main__":
    main()
