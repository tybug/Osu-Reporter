import praw
import config
import secret
import re
import utils
import parser

def main():

	reddit = praw.Reddit(client_id=secret.ID,
                     client_secret=secret.SECRET,
                     user_agent="python:com.tybug.osureporter:v" + secret.VERSION + " (by /u/tybug2)",
                     username=secret.USERNAME,
                     password=secret.PASSWORD)

	subreddit = reddit.subreddit(config.SUB)
	# Iterate over every new submission
	for submission in subreddit.stream.submissions():
		process_submission(submission)

def process_submission(submission):
	title = submission.title
	for strip in config.TITLE_STRIP:
		# Escape for regex
		if(strip in config.ESCAPE_REQUIRED):
			strip = "\\" + strip
		title = re.sub(strip, "", title)

	data = re.split(config.TITLE_SPLIT, title)
	
	if(len(data) < 3): 
		if(config.REPLY_MALFORMAT_COMMENT):
			pass
			# submission.reply(config.REPLY_MALFORMAT_COMMENT)
		return

	print("Gamemode: {}\nPlayer: {}\nType: {}".format(data[0], data[1], data[2]))
	gamemode = parser.parse_gamemode(data[0])
	player = data[1]
	offense = data[2]

	data = parser.parse_user_data(player)
	if(data is None): # user be banned, this will rarely if ever happen, maybe OP was just drunk who knows
		if(config.REPLY_ALREADY_BANNED):
			pass
			# submission.reply(config.REPLY_ALREADY_BANNED)
		return



if __name__ == "__main__":
    main()