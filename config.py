# General Config
SUB = 'OsuReporterTest' # listen for submissions to this sub
SITE = "https://osu.ppy.sh/users/"

# Comment Config (if any of these are set to "", no comment will be left)
# if the title is malformatted.
REPLY_MALFORMAT_COMMENT = ("Your title was misformatted. Please make sure you follow the [formatting rules]"
					"(https://www.reddit.com/r/osureport/comments/5kftu7/changes_to_osureport/)"
					", and repost with a correctly formatted title.")
# if the reported user's page gives 404 at time of report
REPLY_ALREADY_BANNED = ("The user you reported is already restricted!")

# Parse Config
ESCAPE_REQUIRED = ["|", ".", "["] # regex wants escape characters for these
TITLE_STRIP = ["|", "[", "]"] # strip before parsing title, could want to add fancy brackets people use for instance, or if you ever change title formatting
TITLE_SPLIT = "\s+" # split on this regex


# strip before parsing gamemode
GAMEMODE_STRIP = ["osu!"]
# include alternate names for gamemodes (or common mispellings)
GAMEMODE_MATCH_STD = ["standard", "std"]
GAMEMODE_MATCH_CATCH = ["catch", "ctb"]
GAMEMODE_MATCH_MANIA = ["mania"]
GAMEMODE_MATCH_TAIKO = ["taiko"]