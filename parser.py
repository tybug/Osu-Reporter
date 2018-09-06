from config import *
import re
import requests
from secret import KEY

def parse_gamemode(input):
	'''
	Parses the gamemode from the input. 
	Returns the number (as a string) the osu api links expects for each gamemode. 
	If a gamemode cannot be determined by matching against GAMEMODES after stripping chars, returns "0" (osu!standard)
	'''

	input = input.lower()
	for strip in GAMEMODE_STRIP:
		input = re.sub(strip, "", input)

	for gamemode in GAMEMODES:
		if(input in GAMEMODES[gamemode]):
			return gamemode
	
	return "0" # assume std if all else fails



def parse_user_data(username, mode):
	'''
	Returns a list consisting of the json response the osu api gives us when querying data for the given user in the given mode
	'''

	response = requests.get(API + "get_user?k=" + KEY + "&u=" + username + "&m=" + mode)
	user_data = response.json()
	if(not user_data): # empty response (user banned / doesn't exist)
		return

	response = requests.get(API + "get_user_best?k=" + KEY + "&u=" + username + "&m=" + mode)
	top_data = response.json()

	return [user_data[0], top_data] # we could remove extraneous data here...but honestly it's so low volume anyway



def parse_flair_data(offense):
	'''
	Returns a list with [0] being what to name the flair and [1] being the css class of the flair,
	or Cheating if no match could be found and DEFAULT_TO_CHEATING is True, or None otherwise
	'''

	offense = re.split(FLAIR_SPLIT, offense.lower()) # Match on all words; if the title was something like "[osu!std] rttyu-i | Account Sharing/Multi [ Discussion ]" it would check "account", "sharing", "multi", "[", "discussion", "]"
	for flair in FLAIRS:
		if([i for i in offense if i in FLAIRS[flair]]): # SO magic, checks if any item in L1 is also in L2
			return [FLAIRS[flair][-1], flair]

	if(DEFAULT_TO_CHEATING):
		return ["cheating", "Cheating"]



def create_reply(data):
	'''
	Data is a list of lists - element one is user data, the second element is a list of top plays info json
	Returns a reddit reply-ready string, containing the user's profile, a table with relevant stats of that user, 
	a table with that user's top plays, and REPLY_INFO appended
	'''
	user_data = data[0]
	top_data = data[1]
	reply = ("{}'s profile: {}\n\n"
			"| Rank | PP | Playcount |\n"
			":-:|:-:|:-:\n"
			"| #{:,} | {:,} | {:,} |\n\n"
			"| Top Plays | Mods | PP | Date |\n"
			":-:|:-:|:-:|:-:|:-:\n"
			.format(
					user_data["username"],
					USERS + user_data["user_id"],
					int(user_data["pp_rank"]),
					round(float(user_data["pp_raw"])),
					int(user_data["playcount"])
			))


	for play in top_data:
		reply += ("| {} | {} | {:,} | {} |\n"
				 .format(
				 		  parse_map_data(play["beatmap_id"])["title"],
				 		  parse_mods(int(play["enabled_mods"])),
				 		  round(float(play["pp"])),
				 		  play["date"].split(" ")[0].replace("-", "/")
				 ))


	return (reply + REPLY_INFO)



def parse_mods(mods_int):
    """
    Convert a mod integer to a mod string.
    Adapted slightly from https://github.com/christopher-dG/osu-bot. Full credit to christopher.
    """
    mods = []
    for k, v in MODS_INT.items():
        if v & mods_int == v:
            mods.append(k)

    ordered = list(filter(lambda m: m in mods, MOD_ORDER))
    "NC" in ordered and ordered.remove("DT")
    "PF" in ordered and ordered.remove("SD")

    return "+%s" % "".join(ordered) if ordered else "Nomod"



def parse_map_data(map_id):
	response = requests.get(API + "get_beatmaps?k=" + KEY + "&b=" + map_id)
	return response.json()[0]
