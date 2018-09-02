from config import *
import re
import requests
from secret import KEY

def parse_gamemode(input):
	input = input.lower()
	for strip in GAMEMODE_STRIP:
		input = re.sub(strip, "", input)

	for gamemode in GAMEMODES:
		if(input in GAMEMODES[gamemode]):
			return gamemode
	
	return "0" # assume std if all else fails


def parse_user_data(username, mode):
	response = requests.get(API + "get_user?k=" + KEY + "&u=" + username + "&m=" + mode)
	data = response.json()
	if(not data): # empty response
		return

	return data[0] # we could remove extraneous data here...but honestly it's so low volume anyway

def parse_flair_data(offense):
	'''
	Returns a list with [0] being what to name the flair and [1] being the css class of the flair,
	or Cheating if no match could be found and DEFAULT_TO_CHEATING is True, or None otherwise
	'''
	offense = re.split(FLAIR_SPLIT, offense) # Match on all words; if the title was something like "[osu!std] rttyu-i | Account Sharing/Multi [ Discussion ]"
	for flair in FLAIRS:
		if([i for i in offense if i in FLAIRS[flair]]): # SO magic, checks if any item in L1 is also in L2
			return [FLAIRS[flair][-1], flair]

	if(DEFAULT_TO_CHEATING):
		return ["cheating", "Cheating"]


def create_reply(data):
	return ("{}'s profile: {}\n\n"
			"| Rank | PP | Playcount |\n"
			":-:|:-:|:-:\n"
			"| #{:,} | {:,} | {:,} |").format(
										data["username"],
										USERS + data["user_id"],
										int(data["pp_rank"]),
										round(float(data["pp_raw"])),
										int(data["playcount"]))