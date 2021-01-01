import re
import requests
from secret import KEY
import logging as log
from datetime import datetime
from config import (GAMEMODES, FLAIRS, OFFENSES, BLATANT, TITLE_MATCH,
					API_BASE, API_USERS, REPLY_FOOTER, LIMIT_TOP_PLAYS)
from utils import calc_acc, calc_mods, parse_play_rank

from circleguard import Circleguard, ReplayID
# yes yes, globals bad, I know. The rest of this codebase is already crappy
# though so what's the harm in making it a little worse.
# TODO cache? reports are pretty infrequent though, probably not necessary,
# though they do get repeated sometimes.
cg = Circleguard(KEY)

def parse_title_data(title):
	"""
	Returns a list containing the title data, or None if the regex failed to match.
	[Gamemode, player_name, [offense_name, blatant?], [flair_name, css_class]]
	"""
	title_data = TITLE_MATCH.match(title)
	if not title_data: # regex didn't match
		return None

	gamemode = parse_gamemode(title_data.group(1))
	parts = title_data.group(2).split("|", 1) # only split once
	player = parts[0].strip() # take from gamemode to first pipe, remove leading + trailing spaces
	offense = parts[-1].strip() # the last occurence. Identical to info[1] usually,
					   # but when there's no more pipes (ie title is "[osu!std] tybug") info[1] will throw IOOB
	offense_data = parse_offense_data(offense)
	flair_data = parse_flair_data(title)
	return [gamemode, player, offense_data, flair_data]



def parse_gamemode(input_):
	"""
	Parses the gamemode from the given string ("std", "s", "taiko", "mania", "fuits").
	Returns the number (as a string) the osu api links expects for each gamemode.
	If a gamemode cannot be determined by matching against GAMEMODES, returns "0" (osu!standard)
	"""

	for gamemode in GAMEMODES:
		if input_ in GAMEMODES[gamemode]:
			return gamemode

	return "0" # assume std if all else fails



def parse_flair_data(title):
	"""
	Returns a list with [0] being what to name the flair and [1] being the css class of the flair,
	or Cheating if no match could be found
	"""

	# Match on all words; if the title was something like
	# "[osu!std] rttyu-i | Account Sharing/Multi [ Discussion ]" it would
	# check "account", "sharing", "multi", "[", "discussion", "]"
	title = re.split("[|\s/]+", title)
	for flair in FLAIRS:
		if [i for i in title if i in FLAIRS[flair]]: # SO magic, checks if any item in L1 is also in L2
			return [FLAIRS[flair][-1], flair]

	return ["Cheating", "cheating"]



def parse_offense_data(offense):
	"""
	Determines the type of offense contained in the passed string (information after the username in the title).
	Returns a list containing [offense_name, blatant?]
	(whether the title contained anything in BLATANT)
	"""
	offense = re.split("[|\s/]+", offense)
	log.debug("offense split: %s", offense)
	data = ["other"]
	for offense_type in OFFENSES:
		if [i for i in offense if i in OFFENSES[offense_type]]:
			data[0] = offense_type
			break

	# if any element of offense is in blatant
	if [i for i in offense if i in BLATANT]:
		data.append("true")
	else:
		data.append("false")
	return data



def parse_user_data(username, mode, type):
	"""
	Returns a list consisting of the json response the osu api gives us when querying data for the given user in the given mode
	"""
	user_data = []
	# temporary hack until peppy fixes old usernames redirecting properly (https://github.com/ppy/osu-api/issues/280)
	# I have no idea why just appending _ instead of _old works, but it does
	if username.endswith("_old"):
		username = username.replace("_old", "_")
	response = requests.get(API_BASE + "get_user?k=" + KEY + "&u=" + username + "&m=" + mode + "&type=" + type)
	user_data = response.json()

	if not user_data: # empty response (user banned / doesn't exist)
		return

	response = requests.get(API_BASE + "get_user_best?k=" + KEY + "&u=" + username + "&m=" + mode + "&type=" + type)
	top_data = response.json()

	return [user_data[0], top_data] # we could remove extraneous data here...but honestly it's so low volume anyway



def create_reply(text, data, previous_links, mode):
	"""
	Text is the text of the reddit submission
	Data is a list of lists - element one is user data, the second element is a list of top plays info json
	Returns a reddit reply-ready string, containing the user's profile, a table with relevant stats of that user,
	and a table with that user's top plays
	"""

	sim = None
	cheated_match = re.search(r"\(cheated\): https:\/\/osu\.ppy\.sh\/scores\/osu\/(\d+)(\/download)?", text)
	original_match = re.search(r"\(original\): https:\/\/osu\.ppy\.sh\/scores\/osu\/(\d+)\(/download)?", text)

	if cheated_match and original_match:
		cheated_id = int(cheated_match.group(1))
		original_id = int(original_match.group(1))

		cheated = ReplayID(cheated_id)
		original = ReplayID(original_id)
		sim = cg.similarity(cheated, original)


	modes = ["osu", "taiko", "fruits", "mania"] # can't use ?m=0 to specify a gamepage in userpage url unfortunately
	user_data = data[0]
	top_data = data[1]

	# user exists, but hasn't made any plays (ie no pp at all)
	if user_data["pp_raw"] is None:
		reply = "{}'s profile: {}\n\nThis user has not made any plays!".format(user_data["username"], API_USERS + user_data["user_id"] + "/" + modes[int(mode)])
		return reply

	creation_date = datetime.strptime(user_data["join_date"], "%Y-%m-%d %H:%M:%S") #2018-04-15 01:44:28
	difference = datetime.utcnow() - creation_date

	pp_raw = round(float(user_data["pp_raw"]))
	reply = ("{}'s profile: {}\n\n"
			"| Rank | PP | Playtime | Playcount | Country | Joined |\n"
			":-:|:-:|:-:|:-:|:-:|:-:\n"
			"| #{:,} | {} | {} hours | {:,} | {} | ~{} days ago|\n\n"
			"| Top Plays | Mods | PP | Accuracy | Date | Replay Download |\n"
			":-:|:-:|:-:|:-:|:-:|:-:\n"
			.format(
					user_data["username"],
					API_USERS + user_data["user_id"] + "/" + modes[int(mode)],
					int(user_data["pp_rank"]),
					"{:,}".format(pp_raw) if pp_raw != 0 else "0 (inactive)",
					round(int(user_data["total_seconds_played"]) / 60 / 60), # convert to hours
					int(user_data["playcount"]),
					user_data["country"],
					difference.days
			))


	for play in top_data[0:LIMIT_TOP_PLAYS]:

		play_data = requests.get(API_BASE + "get_scores?k=" + KEY + "&b=" + play["beatmap_id"] + "&u=" + user_data["user_id"] + "&m=" + mode + "&mods=" + play["enabled_mods"]).json()[0]
		score_id = play_data["score_id"]
		replay_available = bool(int(play_data["replay_available"]))

		reply += ("| [{}]({}) | {} | {:,} | {}% ({}) | {} | {} |\n"
				 .format(
				 		  parse_map_data(play["beatmap_id"])["title"],
						  "https://osu.ppy.sh/b/{}".format(play["beatmap_id"]),
				 		  calc_mods(play["enabled_mods"]),
				 		  round(float(play["pp"])),
						  calc_acc(play, mode),
						  parse_play_rank(play["rank"]),
				 		  play["date"].split(" ")[0].replace("-", "/"), # "2013-06-22 9:11:16" (api) -> "2013/06/22"
						  "[{}]({})".format(score_id, "https://osu.ppy.sh/scores/osu/{}".format(score_id)) if replay_available else "Unavailable"

				 ))
	reply += "\n\n" + previous_links

	# sim can be 0 which is falsey, so direct comparison to None
	if sim != None:
		reply += (f"\n\nSimilarity of replays [{cheated_id}](https://osu.ppy.sh/scores/osu/{cheated_id}) "
				  f"and [{original_id}](https://osu.ppy.sh/scores/osu/{original_id}): {round(sim, 2)}")

	return reply



def parse_map_data(map_id):
	response = requests.get(API_BASE + "get_beatmaps?k=" + KEY + "&b=" + map_id)
	return response.json()[0]
