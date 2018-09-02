# General Config
DB = "db.db" # relative path to database
SUB = 'OsuReporterTest' # listen for submissions to this sub
API = "https://osu.ppy.sh/api/"
USERS = "https://osu.ppy.sh/users/"
# include alternate names for gamemodes (or common mispellings)
GAMEMODES = {
			 "taiko": ["taiko"],
			 "mania": ["mania"], 
			 "ctb":   ["catch", "ctb"],
			 "std":   ["standard", "std"]
			 }
# css class : [possible matches, ..., ..., flair title]
# Don't bother accounting for meta or other, hard to parse
FLAIRS = {
		  "multi": ["multi-account", "Multiacc", "multi", "Multi-account"],
		  "cheating": ["cheating", "cheater", "Cheating"],
		  "blatant": ["blatant", "Blatant"],
		  "discussion": ["discussion", "Discussion"]
		 }

# If a flair type can't be parsed when first posted, the bot will flair as Cheating if this is True (else won't do anything)
DEFAULT_TO_CHEATING = False
CHECK_INTERVAL = 5 # Check for banned users every x seconds

# Comment Config (if any of these are set to "", no comment will be left)
# if the title is malformatted.
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
