from config import *
import re
import requests
from secret import KEY
from utils import *
import logging as log

def parse_gamemode(input):
	'''
	Parses the gamemode from the given string ("std", "s", "taiko", "mania", "fuits"). 
	Returns the number (as a string) the osu api links expects for each gamemode. 
	If a gamemode cannot be determined by matching against GAMEMODES, returns "0" (osu!standard)
	'''

	for gamemode in GAMEMODES:
		if(input in GAMEMODES[gamemode]):
			return gamemode
	
	return "0" # assume std if all else fails



def parse_user_data(username, mode, type):
	'''
	Returns a list consisting of the json response the osu api gives us when querying data for the given user in the given mode
	'''

	response = requests.get(API + "get_user?k=" + KEY + "&u=" + username + "&m=" + mode + "&type=" + type)
	user_data = response.json()
	if(not user_data): # empty response (user banned / doesn't exist)
		return

	response = requests.get(API + "get_user_best?k=" + KEY + "&u=" + username + "&m=" + mode + "&type=" + type)
	log.debug("response after parsing data for user {}: ".format(username) + response.text)
	top_data = response.json()

	return [user_data[0], top_data] # we could remove extraneous data here...but honestly it's so low volume anyway




def parse_flair_data(offense):
	'''
	Returns a list with [0] being what to name the flair and [1] being the css class of the flair,
	or Cheating if no match could be found and DEFAULT_TO_CHEATING is True, or None otherwise
	'''

	offense = re.split("\s+|/", offense) # Match on all words; if the title was something like "[osu!std] rttyu-i | Account Sharing/Multi [ Discussion ]" it would check "account", "sharing", "multi", "[", "discussion", "]"
	for flair in FLAIRS:
		if([i for i in offense if i in FLAIRS[flair]]): # SO magic, checks if any item in L1 is also in L2
			return [FLAIRS[flair][-1], flair]

	if(DEFAULT_TO_CHEATING):
		return ["cheating", "Cheating"]


def parse_offense_type(offense):
	'''
	Determines the type of offense contained in the passed string (title).
	Returns a list containing the offense at index 0 and whether it was a blatant report or not in index 1 
	(whether the title contained anything in BLATANT)
	'''
	offense = re.split("\s+|/", offense)
	log.debug("offense split: %s", offense)
	data = ["other"]
	for offense_type in OFFENSES:
		log.debug("checking offense against %s", OFFENSES[offense_type])
		if([i for i in offense if i in OFFENSES[offense_type]]):
			data[0] = offense_type
			break

	if([i for i in offense if i in BLATANT]): # if element of offense is in blatant
		data.append("true")
	else:
		data.append("false")

	return data


def create_reply(data, mode):
	'''
	Data is a list of lists - element one is user data, the second element is a list of top plays info json
	Returns a reddit reply-ready string, containing the user's profile, a table with relevant stats of that user, 
	a table with that user's top plays, and REPLY_INFO appended
	'''

	modes = ["osu", "taiko", "fruits", "mania"] # can't use ?m=0 to specify a gamepage in userpage url unfortunately
	user_data = data[0]
	top_data = data[1]
	pp_raw = round(float(user_data["pp_raw"]))
	reply = ("{}'s profile: {}\n\n"
			"| Rank | PP | Playtime | Playcount |\n"
			":-:|:-:|:-:|:-:\n"
			"| #{:,} | {} | {} hours | {:,} |\n\n"
			"| Top Plays | Mods | PP | Accuracy | Date |\n"
			":-:|:-:|:-:|:-:|:-:\n"
			.format(
					user_data["username"],
					USERS + user_data["user_id"] + "/" + modes[int(mode)],
					int(user_data["pp_rank"]),
					"{:,}".format(pp_raw) if pp_raw != 0 else "0 (inactive)",
					round(int(user_data["total_seconds_played"]) / 60 / 60), # convert to hours
					int(user_data["playcount"])
			))

	for play in top_data[0:TOP_PLAY_LIMIT]:
		reply += ("| {} | {} | {:,} | {}% ({}) | {} |\n"
				 .format(
				 		  parse_map_data(play["beatmap_id"])["title"],
				 		  calc_mods(play["enabled_mods"]),
				 		  round(float(play["pp"])),
						  calc_acc(play, mode),
						  parse_play_rank(play["rank"]),
				 		  play["date"].split(" ")[0].replace("-", "/") # "2013-06-22 9:11:16" (api) -> "2013/06/22"
				 ))

	return (reply + REPLY_INFO)



def parse_map_data(map_id):
	log.debug("Parsing map data for map {}".format(map_id))
	response = requests.get(API + "get_beatmaps?k=" + KEY + "&b=" + map_id)
	return response.json()[0]
