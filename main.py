import praw
from config import *
import secret
import re
from parser import parse_flair_data, parse_user_data, parse_gamemode, create_reply
from db import add_submission, add_user, submission_exists, get_all_users, remove_user
import threading

reddit = None # hack to make reddit global (for check_banned())

def main():

	reddit = praw.Reddit(client_id=secret.ID,
                     client_secret=secret.SECRET,
                     user_agent="python:com.tybug.osureporter:v" + secret.VERSION + " (by /u/tybug2)",
                     username=secret.USERNAME,
                     password=secret.PASSWORD)

	subreddit = reddit.subreddit(SUB)
	check_banned() # automatically repeats on interval

	# Iterate over every new submission
	for submission in subreddit.stream.submissions():
		process_submission(submission)


def process_submission(submission):
	if(submission_exists(submission.id)): # Already processed; praw returns the past 100 results for streams, previously iterated over or not
		return

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
			submission.reply(REPLY_MALFORMAT_COMMENT + REPLY_INFO)
		return


	gamemode = parse_gamemode(title_data[0])
	player = title_data[1]
	offense = title_data[2]
	# print("Gamemode: {}\nPlayer: {}\nType: {}".format(gamemode, player, offense))

	# Flair it
	flair_data = parse_flair_data(offense)
	if(flair_data):
		submission.mod.flair(flair_data[0], flair_data[1])



	player_data = parse_user_data(player, gamemode)
	if(player_data is None): # api gives empty json - possible misspelling or user was already banned
		if(REPLY_ALREADY_BANNED):
			submission.reply(REPLY_ALREADY_BANNED + REPLY_INFO)
		return
	# Leave info table comment
	submission.reply(create_reply(player_data))


	# Add to db to check if user was banned on increments
	add_user(player_data["user_id"], submission.id)



def check_banned():
	threading.Timer(CHECK_INTERVAL, check_banned).start() # Calls this function after x seconds, which calls itself. Cheap way to check for banned users on an interval

	for data in get_all_users():

		id = data[0] # user id
		post_id = data[1] # post id
		user_data = parse_user_data(id, "0") # gamemode doesn't matter here since we're just checking for empty response

		if(user_data is None): # user was restricted
			remove_user(id)
			post = praw.Submission(reddit, post_id) # get praw post from id to flair
			post.mod.flair("Resolved", "resolved")



if __name__ == "__main__":
    main()