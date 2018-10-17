import praw
from config import *
import secret
import re
from parser import *
from db import *
import threading
import datetime
import argparse
import logging as log

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--comment", help="doesn't leave comments on posts", action="store_true")
parser.add_argument("-f", "--flair", help="leaves flairs unmodified", action="store_true")

g = parser.add_mutually_exclusive_group()
g.add_argument("-v", "--verbose", help="enables detailed logging", action="store_true")
g.add_argument("-s", "--silent", help="disables all logging", action="store_true")

args = parser.parse_args()

log_level = 20 # INFO
if args.verbose:
	log_level = 10 # DEBUG

log.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p', level=log_level)

# Disable annoying html request logging
log.getLogger("requests").setLevel(log.WARNING)
log.getLogger("urllib3").setLevel(log.WARNING)
log.getLogger("prawcore").setLevel(log.WARNING)


if(args.silent):
	log.disable()


log.info("Logging into reddit")
# keep reddit global
reddit = praw.Reddit(client_id=secret.ID,
                     client_secret=secret.SECRET,
                     user_agent="python:com.tybug.osureporter:v" + secret.VERSION + " (by /u/tybug2)",
                     username=secret.USERNAME,
                     password=secret.PASSWORD)
log.info("Login successful")


def main():
	subreddit = reddit.subreddit(SUB)
	check_banned() # automatically repeats on interval

	# Iterate over every new submission
	for submission in subreddit.stream.submissions():
		process_submission(submission, not args.comment, not args.flair)




def process_submission(submission, shouldComment, shouldFlair):
	link = "https://old.reddit.com" + submission.permalink
	if(submission_exists(submission.id)): # Already processed; praw returns the past 100 results for streams, previously iterated over or not
		log.debug("Submission %s is already processed", submission.id)
		return

	log.info("Processing submission %s", link)
	log.debug("Adding post %s to db", submission.id)
	add_submission(submission.id)


	title = submission.title
	for strip in TITLE_STRIP:
		# Escape for regex
		if(strip in ESCAPE_REQUIRED):
			strip = "\\" + strip
		title = re.sub(strip, "", title)


	title_data = re.split(TITLE_SPLIT, title)
	if(len(title_data) < 3): 
		if(REPLY_MALFORMAT_COMMENT and shouldComment):
			submission.reply(REPLY_MALFORMAT_COMMENT + REPLY_INFO)
		return


	gamemode = parse_gamemode(title_data[0])
	player = title_data[1]
	offense = title_data[2]

	# Flair it
	flair_data = parse_flair_data(offense)
	if(flair_data):
		if(submission.link_flair_text == "Resolved"): # don't overwrite resolved flairs
			log.debug("Neglecting to flair %s as %s, it is already flaired resolved", submission.permalink, flair_data[0])
		elif shouldFlair:
			submission.mod.flair(flair_data[0], flair_data[1])


	if([i for i in title_data if i in REPLY_IGNORE]): # if the title has any blacklisted words (for discssion threads), don't process it further
		log.debug("Not processing %s further; the title contained blacklisted discussion words", link)
		return
	
	player_data = parse_user_data(player, gamemode, "string")
	if(player_data is None): # api gives empty json - possible misspelling or user was already restricted
		log.debug("User with name %s was already restricted at the time of submission", player)
		if(REPLY_ALREADY_RESTRICTED and shouldComment):
			log.debug("Leaving already banned comment")
			submission.reply(REPLY_ALREADY_RESTRICTED.format(USERS + player) + REPLY_INFO)
		return

	log.debug("Replying with data for %s", player)
	if shouldComment:
		submission.reply(create_reply(player_data))

	# only add to db if it's not already there
	if(not user_exists(player_data[0]["user_id"])):
		log.debug("Adding user with name %s and id %s to db to track potential future restriction", player, player_data[0]["user_id"])
		add_user(player_data[0]["user_id"], submission.id, submission.created_utc)



def check_banned():
	log.info("Checking for restricted users..")
	threading.Timer(CHECK_INTERVAL, check_banned).start() # Calls this function after x seconds, which calls itself. Cheap way to check for banned users on an interval

	for data in get_all_users():
		log.debug("Checking if user %s is restricted", data[0])
		id = data[0] # user id
		post_id = data[1] # post id
		post_date = data[2] # post submission date

		post_date = int(float(post_date))
		difference = datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(post_date)
		if(difference.total_seconds() > LIMIT_DAYS * 24 * 60 * 60): # compare seconds
			log.info("Removing user %s from database, over time limit", id)
			remove_user(id)
			return


		user_data = parse_user_data(id, "0", "id") # gamemode doesn't matter here since we're just checking for empty response

		if(user_data is None): # user was restricted
			log.info("Removing user %s from database, user restricted", id)
			remove_user(id)
			post = praw.models.Submission(reddit, post_id) # get praw post from id to flair
			log.info("Flairing post %s as resolved", post.permalink)
			if(shouldFlair):
				post.mod.flair("Resolved", "resolved")


	# Might as well forward pms here...already have an automated function, why not?
	for message in reddit.inbox.unread():		
		log.info("Forwarding message by %s to %s", message.author, AUTHOR)
		reddit.redditor(AUTHOR).message("Forwarding message to me from u/{}".format(message.author), message.body)
		message.mark_read()



if __name__ == "__main__":
	main()