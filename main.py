import argparse
import logging
import time
import threading
from prawcore.exceptions import RequestException, ServerError, ResponseException
import sys
import json
import stats
import praw
import secret
import re
from db import DB
import datetime
from report import Report
from sheriff import Sheriff
from old_report import OldReport
from config import (VERSION, SUB, LIMIT_DAYS, API_USERS, CHECK_INTERVAL, AUTHOR,
	REJECT_BLACKLISTED, REJECT_MALFORMATTED, REJECT_REPORTED, REJECT_RESTRICTED,
	REPLY_MALFORMATTED, REPLY_REPORTED, REPLY_RESTRICTED)


parser = argparse.ArgumentParser()
parser.add_argument("-c", "--comment", help="doesn't leave comments on submissions", action="store_true")
parser.add_argument("-f", "--flair", help="leaves flairs unmodified. No effect when set with --sweep", action="store_true")
parser.add_argument("-d", "--debug", help="runs in debug mode. Equivelant to -cfv --leadless", action="store_true")
parser.add_argument("-p", "--from-id", help="processes a single post from given id", dest="post_id")
parser.add_argument("--leadless", help="doesn't modify the database while running", action="store_true")
# parser.add_argument("-t", "--test", help="runs test suite and exits", action="store_true")

g1 = parser.add_mutually_exclusive_group()
g1.add_argument("--stats", help="calculates and displays statistics from the db", action="store_true")
g1.add_argument("--sweep", help="runs through the past 100 submissions and flairs them appropriately, ignoring resolved threads. Sets --comment as well.", action="store_true")


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
	args.leadless = True

if args.sweep:
	args.comment = True



log_level = 20 # INFO
if args.verbose:
	log_level = 10 # DEBUG


log = logging.getLogger()
log.setLevel(log_level)

formatter = logging.Formatter(fmt='[%(levelname)s] %(asctime)s %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

# Disable annoying html request logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("prawcore").setLevel(logging.WARNING)


if(args.silent):
	logging.disable()


log.info("Logging into reddit")
# keep reddit global
reddit = praw.Reddit(client_id=secret.ID,
                     client_secret=secret.SECRET,
                     user_agent="linux:com.tybug.osureporter:v" + VERSION + " (by /u/tybug2)",
                     username=secret.USERNAME,
                     password=secret.PASSWORD)

# keep submission stream global as well. PRAW streams save internal state, so if there's an error we can re-use the stream without duplicating thread checks.
subreddit = reddit.subreddit(SUB)
submission_stream = subreddit.stream.submissions()

# db interface with a single connection and cursor. Only create this once to limit connections, then pass it to each recorder object (reports and sheriffs)	 
DB_MAIN = DB(args.leadless)

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
		process_submission(praw.models.Submission(reddit, id=args.post_id), not args.comment, not args.flair)
		sys.exit(0)


	try:
		check_banned(not args.comment, not args.flair) # repeats on CHECK_INTERVAL minutes interval
	except KeyboardInterrupt:
		log.info("Received SIGINT, terminating")
		sys.exit(0)
		
	# Iterate over every new submission forever. Keeps the bot very low mantainence, as the praw stream can error occasionally 
	while True:

		# two layers of exception handling, one for the processing and one for the submission stream. Probably a relatively dirty way to do it - 
		# (all error handling should happen in process_submission?) - but a I said it keeps the bot low mantainence.
		try:
			for submission in submission_stream:
				try:
					if(DB_MAIN.submission_exists(submission.id)): # Already processed; praw returns the past 100 results for streams, previously iterated over or not
						log.debug("Submission {} is already processed".format(submission.id))
						continue
					process_submission(submission, not args.comment, not args.flair)
				except RequestException as e:
					log.warning("Request exception while processing submission {}: {}. Waiting 10 seconds".format(submission.id, str(e)))
					time.sleep(10)
				except ServerError as e:
					log.warning("Server error while processing submission {}: {}. Reddit likely under heavy load".format(submission.id, str(e)))
				except json.decoder.JSONDecodeError as e:
					log.warning("JSONDecode exception while processing submission {}: {}.".format(submission.id, str(e)))

		except KeyboardInterrupt:
			log.info("Received SIGINT, terminating")
			sys.exit(0)
		except RequestException as e:
			log.warning("Request exception in submission stream: {}. Waiting 10 seconds".format(str(e)))
			time.sleep(10)
		except ServerError as e:
			log.warning("Server error in submission stream: {}.".format(str(e)))
		except json.decoder.JSONDecodeError as e:
			log.warning("JSONDecode exception in submission stream: {}.".format(str(e)))

		time.sleep(60 * 2) # sleep for two minutes, give any connection issues some time to resolve itself

		

def process_submission(submission, shouldComment, shouldFlair):
	'''
	Processes the given reddit submission. 
	'''

	report = Report(submission, shouldComment, shouldFlair, DB_MAIN)
	report.mark_read()


	if(report.has_blacklisted_words()): # for discssion threads etc
		report.reject(REJECT_BLACKLISTED)
		return
		

	if(report.check_malformatted()): # title wasn't properly formatted
		report.reply(REPLY_MALFORMATTED).reject(REJECT_MALFORMATTED)
		return

	# Flair it based on what was in the title
	report.flair()

	if(report.check_restricted()): # api gives empty json - possible misspelling or user was already restricted
		report.reply(REPLY_RESTRICTED.format(API_USERS + report.username)).reject(REJECT_RESTRICTED)
		return

	previous_links = report.generate_previous_links()
	
	previous_id = report.check_duplicate() # returns post id from db query
	if(previous_id):
		log.debug("User reported in post {} was already reported in the past {} days in post {}".format(report.post_id, LIMIT_DAYS, previous_id))
		report.reply(REPLY_REPORTED.format(API_USERS + report.user_id, "https://redd.it/" + str(previous_id), previous_links, LIMIT_DAYS))
		return
	
	# all special cases handled, finally reply with the data and add to db for sheriff to check
	report.reply_data_and_mark()



def check_banned(shouldComment, shouldFlair):
	thread = threading.Timer(CHECK_INTERVAL * 60, check_banned, [shouldComment, shouldFlair]) 
	thread.daemon = True # Dies when the main thread dies
	thread.start()
	
	# make a new one for every thread so we don't get two threads modifying at the same time
	# generating a new connection every CHECK_INTERVAL minutes isn't terribly expensive
	DB_CHECK = DB(args.leadless)
	sheriff = Sheriff(DB_CHECK)

	records = sheriff.get_records()
	log.debug("")
	log.info("Checking " + str(len(records)) + " posts for restrictions")
	for record in records: # only retrieves records in the past month
		post_id = record[0]
		log.debug("Checking post {}".format(post_id))
		submission = reddit.submission(id=post_id)
		report = OldReport(submission, shouldComment, shouldFlair, record, DB)
		
		
		if(report.check_restricted()): # user was restricted
			# resolve the original post (the one we checked)
			report.resolve()
			# resolve all previous reports on the same guy, regardless of time limit
			for _record in report.get_user_records():
				_report = OldReport(reddit.submission(id=_record[1]), shouldComment, shouldFlair, _record, DB)
				_report.resolve()



	log.debug("Done. Checking mail")
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
		if(DB_MAIN.submission_exists(submission.id)):
			continue
		process_submission(submission, not args.comment, True)
		


if __name__ == "__main__":
	main()