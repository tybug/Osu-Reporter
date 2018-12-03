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
parser.add_argument("-f", "--flair", help="leaves flairs unmodified. No effect when set with --sweep", action="store_true")
parser.add_argument("-d", "--debug", help="runs in debug mode. Equivelant to -cfv", action="store_true")
parser.add_argument("-p", "--from-post", help="processes a single post from given id", dest="post_id")
# parser.add_argument("-t", "--test", help="runs test suite and exits", action="store_true")

g1 = parser.add_mutually_exclusive_group()
g1.add_argument("--stats", help="calculates and displays statistics from the db", action="store_true")
g1.add_argument("--sweep", help="runs through the past 100 posts and flairs them appropriately, ignoring resolved threads. Does not leave comments", action="store_true")


g2 = parser.add_mutually_exclusive_group()
g2.add_argument("-v", "--verbose", help="enables detailed logging", action="store_true")
g2.add_argument("-s", "--silent", help="disables all logging", action="store_true")

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


log.info("Logging into reddit")
# keep reddit global
reddit = praw.Reddit(client_id=secret.ID,
                     client_secret=secret.SECRET,
                     user_agent="linux:com.tybug.osureporter:v" + secret.VERSION + " (by /u/tybug2)",
                     username=secret.USERNAME,
                     password=secret.PASSWORD)
					 
log.info("Login successful")


def main():

	if(args.sweep):
		sweep()
		sys.exit(0)

	if(args.stats):
		stats.main()
		sys.exit(0)

	if(args.post_id):
		log.debug("Processing single submission {}".format(args.post_id))
		process_submission(praw.models.Submission(reddit, id=args.post_id), not args.comment, not args.flair, True)
		sys.exit(0)



	subreddit = reddit.subreddit(SUB)
	# Iterate over every new submission
	try:
		check_banned(not args.flair) # repeats on CHECK_INTERVAL minutes interval
		for submission in subreddit.stream.submissions():
			try:
				if(submission_exists(submission.id)): # Already processed; praw returns the past 100 results for streams, previously iterated over or not
					log.debug("Submission {} is already processed".format(submission.id))
					continue
				process_submission(submission, not args.comment, not args.flair, True)
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
		sys.exit(0)

		

def process_submission(submission, shouldComment, shouldFlair, modifyDB):
	link = "https://old.reddit.com" + submission.permalink

	log.debug("")
	log.info("Processing submission {}".format(link))
	log.debug("Adding post {} to db".format(submission.id))
	add_submission(submission.id)


	title = submission.title.lower()
	log.debug("Lowered title: {}".format(title))
	title_data = parse_title_data(title)


	if(title_data is None): # regex didn't match
		log.debug("Replying malformatted to post {}, returning".format(submission.id))
		if(REPLY_MALFORMAT_COMMENT):
			reply(submission, REPLY_MALFORMAT_COMMENT + REPLY_INFO, shouldComment)
		return

	gamemode = title_data[0]
	player = title_data[1]
	offense_data = title_data[2]
	flair_data = title_data[3]
	log.debug("Gamemode, player, offense_data, flair_data: [{}, {}, {}, {}]".format(gamemode, player, offense_data, flair_data))


	# Flair it
	if(flair_data):
		if(submission.link_flair_text == "Resolved"): # don't overwrite resolved flairs
			log.info("Neglecting to flair submission {} as {}, it is already flaired resolved, returning".format(submission.id, flair_data[0]))
			return
		elif shouldFlair:
			submission.mod.flair(flair_data[0], flair_data[1])



	if([i for i in title.split(" ") if i in REPLY_IGNORE]): # if the title has any blacklisted words (for discssion threads), don't process it further
		log.info("title of {} contained blacklisted discussion words, returning".format(link))
		return

	player_data = []
	try:
		player_data = parse_user_data(player, gamemode, "string")
	except Exception as e:
		log.warning("Exception while parsing user data for user {}: ".format(player) + str(e))

	if(player_data is None): # api gives empty json - possible misspelling or user was already restricted
		log.info("User with name {} was already restricted at the time of submission, replying and returning".format(player))
		if(REPLY_ALREADY_RESTRICTED):
			log.debug("Leaving already banned comment")
			reply(submission, REPLY_ALREADY_RESTRICTED.format(USERS + player) + REPLY_INFO, shouldComment)
		return

	player_id = player_data[0]["user_id"]
	if(user_exists(player_id)):
		log.debug("User with id {} and name {} already exists".format(player_id, player))
		previous_id = post_from_user(player_id)
		previous_submission = reddit.submission(id=previous_id)
		# not foolproof by any means - RE https://www.reddit.com/r/redditdev/comments/44a7xm/praw_how_to_tell_if_a_submission_has_been_removed/, but good enough for us
		if(previous_submission.selftext == "[deleted]"): 
			if(modifyDB):
				log.debug("previous submission at {} was deleted, removing user {} so a new entry can be placed".format(previous_id, player_id))
				remove_user(player_id) # so we can add the newer post in a further half dozen lines	
		else:
			log.info("User with id {} already has an active thread at {}, referring OP to it, returning".format(player_id, previous_id))
			reply(submission, REPLY_ALREADY_REPORTED.format(USERS + player, REDDIT_URL_STUB + "/" + previous_id, LIMIT_DAYS) + REPLY_INFO, shouldComment)
			return



	log.info("Replying with data for {}".format(player))
	reply(submission, create_reply(player_data, gamemode), shouldComment)

	if(modifyDB):
		log.debug("Adding user with name {}, id {}, post id {}, offense {}, blatant? {}, reported by {}".format(player, player_id,
				  submission.id, offense_data[0], offense_data[1], submission.author.name))
		# we can assume the id isn't in there already (avoiding UNIQUE_CONSTRAINT) because the if(user_exists) check returns or deletes it
		add_user(player_id, submission.id, submission.created_utc, offense_data[0], offense_data[1], submission.author.name)



def reply(submission, message, shouldReply):
	if(not shouldReply):
		log.debug("flag set; not leaving reply")
		return

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

		try:
			user_data = parse_user_data(id, "0", "id") # gamemode doesn't matter here since we're just checking for empty response
		except Exception as e:
			log.warning("Exception while parsing user data for user {}: ".format(id) + str(e))
			continue

# Check if the user was restrictedfirst, then remove them from the db if over time limit. When running from an old database, old threads will still get marked resolved instaed of thrown out.
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
		elif(difference.total_seconds() > LIMIT_DAYS * 24 * 60 * 60): # compare seconds
			log.info("Removing user {} from database, over time limit".format(id))
			remove_user(id)
			log.debug("Adding not-restricted statistic for user {} on post {}, reported at {}, restricted at {}, reported for {}, blatant? {}, reported by {}"
					.format(id, post_id, post_date, "n/a", offense_type, blatant, reportee))
			add_stat(id, post_id, post_date, "n/a", offense_type, blatant, reportee)
			continue


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




def sweep():
	subreddit = reddit.subreddit(SUB)
	for submission in subreddit.new(limit=100):
		process_submission(submission, False, True, False)
		


if __name__ == "__main__":
	main()