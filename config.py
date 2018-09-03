# General Config
DB = "db.db" # relative path to database
SUB = 'osureport' # listen for submissions to this sub
API = "https://osu.ppy.sh/api/"
USERS = "https://osu.ppy.sh/users/"
AUTHOR = "tybug2" # reddit user to forward replies and dms to
LIMIT_DAYS = 2 # stop checking threads for invalid after they're 2 days old

# include alternate names for gamemodes (or common mispellings)
GAMEMODES = {
			 "0": ["standard", "std"],
			 "1": ["taiko"],
			 "3": ["mania", "m"], 
			 "2": ["catch", "ctb", "fruits"]
			 }
# css class : [possible matches, ..., ..., flair title]
# Don't bother accounting for meta or other, hard to parse
# Prioritizes flair types higher in the list - if a title contains both "discussion" and "multiacc", it will be flaired as "discussion"
FLAIRS = {
		  "discussion": ["discussion", "Discussion"],
		  "blatant": ["blatant", "Blatant"],
		  "multi": ["multi-account", "multiacc", "multi", "multiaccount", "Multi-account"],
		  "cheating": ["cheating", "cheater", "Cheating"]
		 }

# If a flair type can't be parsed when first posted, the bot will flair as Cheating if this is True (else won't do anything)
DEFAULT_TO_CHEATING = False
CHECK_INTERVAL = 900 # Check for banned users every 15 minutes (900 seconds)

# Comment Config (if any of these are set to "", no comment will be left)
# Appended to every comment
REPLY_INFO = ("\n\n***\n\n"
			  "[^Source](https://github.com/tybug/Osu-Reporter) ^| [^Developer](https://reddit.com/u/tybug2) ^| ^(Reply to leave feedback)")

# if the title is malformatted
REPLY_MALFORMAT_COMMENT = ("Your title was misformatted. Please make sure you follow the [formatting rules]"
					"(https://www.reddit.com/r/osureport/comments/5kftu7/changes_to_osureport/)"
					", and repost with a correctly formatted title.")
# if the reported user's page gives 404 at time of report
REPLY_ALREADY_BANNED = ("The user you reported is already restricted, or doesn't exist!")


# Parse Config
ESCAPE_REQUIRED = ["|", ".", "["] # regex wants escape characters for these
TITLE_STRIP = ["|", "[", "]"] # strip before parsing title, could want to add fancy brackets people use for instance, or if you ever change title formatting
TITLE_SPLIT = "\s+" # split on this regex
GAMEMODE_STRIP = ["osu!", "o!"] # strip before parsing gamemode
FLAIR_SPLIT = "/\s+" # split for flair word search on this regex
