import re

# General Config
DB = "db.db" # relative path to database
SUB = 'osureport' # listen for submissions to this sub
API = "https://osu.ppy.sh/api/"
USERS = "https://osu.ppy.sh/users/"
AUTHOR = "tybug2" # reddit user to forward replies and dms to
LIMIT_DAYS = 31 # stop checking threads for invalid after they're x days old
TOP_PLAY_LIMIT = 5 # how many top plays to provide pp data for
REDDIT_URL_STUB = "https://www.reddit.com/r/" + SUB
# include alternate names for gamemodes (or common mispellings)
GAMEMODES = {
			 "0": ["standard", "std", "s"],
			 "1": ["taiko", "t"],
             "2": ["catch", "ctb", "fruits", "c"],
			 "3": ["mania", "m"]
			 }
             
# css class : [possible matches, ..., ..., flair title]
# Don't bother accounting for meta or other, hard to parse
# Prioritizes flair types higher in the list - if a title contains both "discussion" and "multiacc", it will be flaired as "discussion"
FLAIRS = {
          "meta": ["[meta]", "Meta"],
		  "discussion": ["discussion", "Discussion"],
		  "blatant": ["blatant", "Blatant"],
		  "multi": ["multi-account", "multiacc", "multi", "multiaccount", "Multi-account"],
		  "cheating": ["cheating", "cheater", "Cheating"]
		 }


# for parsing offense type
# TODO redo how offenses are handled...don't tier them, check for the existence of any of them and insert into db as binary value.
# do a simple `for offense in OFFENSES:
#                 for word in OFFENSES[offense]:
#                     if word in title:
#                         #binary bit manipulation`
OFFENSES = {
            "multi": ["multi", "multiacc", "multi-account", "multiaccount"],
            "assist": ["assist"], # aim assist
            "spinhack": ["spinhack", "spin", "spin-hack", "spinhacking", "spin-hacking", ],
            "stealing": ["stealing", "steal"],
            "editing": ["editing", "edit", "correction", "replay-editing"],
            "relax": ["relax", "ur", "cv", "rx"],
            "auto": ["auto"],
            "timewarp": ["warp", "timewarp", "time-warp"]
            }
BLATANT = ["blatant", "blat", "obvious"]


REPLY_IGNORE = ["megathread", "discussion", "multiple", "[meta]"] # don't comment if the title contains these

# If a flair type can't be parsed when first posted, the bot will flair as Cheating if this is True (else won't do anything)
DEFAULT_TO_CHEATING = True
CHECK_INTERVAL = 15 # Check for banned users every 15 minutes

# Comment Config (if any of these are set to "", no comment will be left)
# Appended to every comment
REPLY_INFO = ("\n\n***\n\n"
			  "[^Source](https://github.com/tybug/Osu-Reporter) ^| [^Developer](https://reddit.com/u/tybug2) ^| ^(Reply to leave feedback)")

# if the title is malformatted
REPLY_MALFORMAT_COMMENT = ("Your title was misformatted. Please make sure you follow the [formatting rules]"
					"(https://www.reddit.com/r/osureport/comments/5kftu7/changes_to_osureport/)"
					", and repost with a correctly formatted title.\n\n"
                    "| Troubleshooting ||\n"
                    ":-:|:-:\n"
                    "| This is clearly a meta or discussion thread. How can I get the bot to recognize this? |"
                    "Have one of the following (case insensitive) in your title and the bot will pass over your post, and not leave annoying comments: **" +  ", ".join(REPLY_IGNORE) + "**.&nbsp;Meta threads should be posted with [Meta] at the beginning of the title. |\n"
                    "| My title looks fine...what am I missing? | Make sure you are using the right brackets ([]) and do not have spaces in your gamemode. A title can start with [osu!std], but not [osu! std]")
# if the reported user's page gives not found at time of report
REPLY_ALREADY_RESTRICTED = ("The [user you reported]({}) is already restricted, or doesn't exist!")

# if the reported user already has a report on him in the past LIMIT_DAYS days. Format: profile_link, previous_post_link, LIMIT_DAYS
REPLY_ALREADY_REPORTED = ("The [user you reported]({}) already has a recent thread on him. "
                            "[Please contribute your evidence and thoughts to that thread instead!]({})\n\nNote: A new report thread can be made when"
                            " the old one is {} days old.")
# if comments by the bot should be stickied
STICKY = True

# Parse Config
TITLE_MATCH = re.compile("\[(?:osu|o)!(standard|std|s|taiko|t|mania|m|catch|ctb|fruits|c)](.*)")


# Full credit for these two to Christoper (https://github.com/christopher-dG/osu-bot)
MODS_INT = {
    "": 1 >> 1,
    "NF": 1 << 0,
    "EZ": 1 << 1,
    "TD": 1 << 2,
    "HD": 1 << 3,
    "HR": 1 << 4,
    "SD": 1 << 5,
    "DT": 1 << 6,
    "RX": 1 << 7,
    "HT": 1 << 8,
    "NC": 1 << 6 | 1 << 9,  # DT is always set along with NC.
    "FL": 1 << 10,
    "AT": 1 << 11,
    "SO": 1 << 12,
    "AP": 1 << 13,
    "PF": 1 << 5 | 1 << 14,  # SD is always set along with PF.
    "V2": 1 << 29
}

MOD_ORDER = [
    "EZ", "HD", "HT", "DT", "NC", "HR", "FL", "NF",
    "SD", "PF", "RX", "AP", "SO", "AT", "V2", "TD",
]