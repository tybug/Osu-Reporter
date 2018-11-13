import praw
from config import *
import secret
import re
from parser import *
from db import *
import datetime
import argparse
import logging as log
import time
import threading
from prawcore.exceptions import RequestException, ServerError, ResponseException
import sys
import json
import stats
# import test_module

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--comment", help="doesn't leave comments on posts", action="store_true")
parser.add_argument("-f", "--flair", help="leaves flairs unmodified", action="store_true")
parser.add_argument("-d", "--debug", help="runs in debug mode. Equivelant to -cfv", action="store_true")
parser.add_argument("--stats", help="calculates and displays statistics from the db", action="store_true")

# parser.add_argument("-t", "--test", help="runs test suite and exits", action="store_true")

g = parser.add_mutually_exclusive_group()
g.add_argument("-v", "--verbose", help="enables detailed logging", action="store_true")
g.add_argument("-s", "--silent", help="disables all logging", action="store_true")

args = parser.parse_args()

# if args.test:
# 	test_module.run()
# 	sys.exit()

if args.debug:
	args.verbose = True
	args.comment = True
	args.flair = True

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

if(args.stats):
	stats.main()
	sys.exit()

log.info("Logging into reddit")
# keep reddit global
reddit = praw.Reddit(client_id=secret.ID,
                     client_secret=secret.SECRET,
                     user_agent="linux:com.tybug.osureporter:v" + secret.VERSION + " (by /u/tybug2)",
                     username=secret.USERNAME,
                     password=secret.PASSWORD)
log.info("Login successful")


def main():
	subreddit = reddit.subreddit(SUB)
	# Iterate over every new submission
	try:
		check_banned(not args.flair) # repeats on CHECK_INTERVAL minutes interval
		for submission in subreddit.stream.submissions():
			try:
				process_submission(submission, not args.comment, not args.flair)
			except RequestException as e:
				log.warning("Request exception in submission stream: {}. Waiting 10 seconds".format(str(e)))
				time.sleep(10)
			except ResponseException as e:
				log.warning("Response exception in submission stream: {}. Ignoring; likely dropped a comment.".format(str(e)))
			except ServerError as e:
				log.warning("Server error in submission stream: {}. Reddit likely under heavy load, ignoring".format(str(e)))
			except json.decoder.JSONDecodeError as e:
				log.warning("JSONDecode exception in submission stream: {}.".format(str(e)))

	except KeyboardInterrupt:
		log.info("Received SIGINT, terminating")
		sys.exit()

		

def process_submission(submission, shouldComment, shouldFlair):
	link = "https://old.reddit.com" + submission.permalink
	if(submission_exists(submission.id)): # Already processed; praw returns the past 100 results for streams, previously iterated over or not
		log.debug("Submission {} is already processed".format(submission.id))
		return

	log.debug("")
	log.info("Processing submission {}".format(link))
	log.debug("Adding post {} to db".format(submission.id))
	add_submission(submission.id)


	title = submission.title.lower()
	log.debug("Lowered title: {}".format(title))
	
	title_data = TITLE_MATCH.match(title)
	if(not title_data): # regex didn't match
		log.debug("Replying malformatted to post {}".format(submission.id))
		if(REPLY_MALFORMAT_COMMENT and shouldComment):
			reply(submission, REPLY_MALFORMAT_COMMENT + REPLY_INFO)
		return


	gamemode = parse_gamemode(title_data.group(1))
	info = title_data.group(2).split("|", 1) # only split once
	player = info[0].strip() # take from gamemode to first pipe, remove leading + trailing spaces
	offense = info[-1] # the last occurence. Identical to info[1] usually, 
					   # but when there's no more pipes (ie title is "[osu!std] tybug") info[1] will throw IOOB
	log.debug("Gamemode, player, offense: [{}, {}, {}]".format(gamemode, player, offense))


	# Flair it
	flair_data = parse_flair_data(offense)
	if(flair_data):
		if(submission.link_flair_text == "Resolved"): # don't overwrite resolved flairs
			log.debug("Neglecting to flair submission {} as {}, it is already flaired resolved".format(submission.id, flair_data[0]))
		elif shouldFlair:
			submission.mod.flair(flair_data[0], flair_data[1])



	if([i for i in title.split(" ") if i in REPLY_IGNORE]): # if the title has any blacklisted words (for discssion threads), don't process it further
		log.debug("Not processing {} further; the title contained blacklisted discussion words".format(link))
		return
	

	try:
		player_data = parse_user_data(player, gamemode, "string")
	except Exception as e:
		logging.warning("Exception while parsing user data for user {}: ".format(player) + str(e))

	if(player_data is None): # api gives empty json - possible misspelling or user was already restricted
		log.debug("User with name {} was already restricted at the time of submission, not processing further".format(player))
		if(REPLY_ALREADY_RESTRICTED and shouldComment):
			log.debug("Leaving already banned comment")
			reply(submission, REPLY_ALREADY_RESTRICTED.format(USERS + player) + REPLY_INFO)
		return

	player_id = player_data[0]["user_id"]
	if(user_exists(player_id)):
		log.debug("User with id {} and name {} already exists".format(player_id, player))
		previous_id = post_from_user(player_id)
		previous_submission = reddit.submission(id=previous_id)
		# not foolproof by any means - RE https://www.reddit.com/r/redditdev/comments/44a7xm/praw_how_to_tell_if_a_submission_has_been_removed/, but good enough for us
		if(previous_submission.selftext == "[deleted]"): 
			log.debug("previous submission at {} was deleted, removing user {} so a new entry can be placed".format(previous_id, player_id))
			remove_user(player_id) # so we can add the newer post in a further half dozen lines	
		else:
			log.debug("User with id {} already has an active thread at {}, referring OP to it".format(player_id, previous_id))
			reply(submission, REPLY_ALREADY_REPORTED.format(USERS + player, REDDIT_URL_STUB + "/" + previous_id, LIMIT_DAYS) + REPLY_INFO)
			return



	log.debug("Replying with data for {}".format(player))
	if shouldComment:
		reply(submission, create_reply(player_data, gamemode))


	offense_data = parse_offense_type(offense) # take rest of title and make it into single offense
	log.debug("Adding user with name {}, id {}, post id {}, offense {}, blatant? {}, reported by {}".format(player, player_id,
				 submission.id, offense_data[0], offense_data[1], submission.author.name))
	# we can assume the id isn't in there already (avoiding UNIQUE_CONSTRAINT) because the if(user_exists) check returns or deletes it
	add_user(player_id, submission.id, submission.created_utc, offense_data[0], offense_data[1], submission.author.name)



def reply(submission, message):
	comment = submission.reply(message)
	if(STICKY):
		log.debug("Stickying comment {}".format(comment.id))
		comment.mod.distinguish(how="yes", sticky=True)




def check_banned(shouldFlair):
	thread = threading.Timer(CHECK_INTERVAL * 60, check_banned, [shouldFlair]) 
	thread.daemon = True # Dies when the main thread dies
	thread.start()
	log.debug("")
	log.debug("Checking restricted users and new messages..")
	
	for data in get_all_users():
		# log.debug("Checking if user {} is restricted".format(data[0])) TODO replace with lower level .trace
		id = data[0] # user id
		post_id = data[1] # post id
		post_date = data[2] # post submission date
		offense_type = data[3]
		blatant = data[4]
		reportee = data[5]

		post_date = int(float(post_date))
		difference = datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(post_date)
		if(difference.total_seconds() > LIMIT_DAYS * 24 * 60 * 60): # compare seconds
			log.info("Removing user {} from database, over time limit".format(id))
			remove_user(id)
			log.debug("Adding not-restricted statistic for user {} on post {}, reported at {}, restricted at {}, reported for {}, blatant? {}, reported by {}"
					.format(id, post_id, post_date, "n/a", offense_type, blatant, reportee))
			add_stat(id, post_id, post_date, "n/a", offense_type, blatant, reportee)
			continue

		try:
			user_data = parse_user_data(id, "0", "id") # gamemode doesn't matter here since we're just checking for empty response
		except Exception as e:
			logging.warning("Exception while parsing user data for user {}: ",format(id) + str(e))
			continue

		if(user_data is None): # user was restricted
			log.info("Removing user {} from database, user restricted".format(id))
			remove_user(id)
			post = praw.models.Submission(reddit, post_id) # get praw post from id, to flair
			log.info("Flairing post {} as resolved".format(post.id))
			if(shouldFlair):
				post.mod.flair("Resolved", "resolved")																						
				log.debug("Adding restricted statistic for user {} on post {}, reported at {}, restricted at {}, reported for {}, blatant? {}, reported by {}"
				 			.format(id, post_id, post_date, time.time(), offense_type, blatant, reportee))
												# current utc time
				add_stat(id, post_id, post_date, time.time(), offense_type, blatant, reportee)


	# Might as well forward pms here...already have an automated function, why not?
	for message in reddit.inbox.unread():	
		isComment = isinstance(message, praw.models.Comment)	
		type = "reply" if isComment else "PM"
		if(message.author == AUTHOR):
			log.debug("Not forwarding {} by AUTHOR ({})".format(type, AUTHOR))
			return
		
		log.info("Forwarding {} by {} to {}".format(type, message.author, AUTHOR))

		reddit.redditor(AUTHOR).message("Forwarding {} from u/{}".format(type, message.author),
									 "[" + message.body + "]({})".format("https://reddit.com" + message.context) if isComment else message.body)
		message.mark_read()
	log.debug("..done")




if __name__ == "__main__":
	main()