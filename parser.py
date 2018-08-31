import config
import re
import utils

def parse_gamemode(input):
	input = input.lower()
	for strip in config.GAMEMODE_STRIP:
		input = re.sub(strip, "", input)
	if(input in config.GAMEMODE_MATCH_STD):
		return utils.GAMEMODE_STD
	if(input in config.GAMEMODE_MATCH_CATCH):
		return utils.GAMEMODE_CATCH
	if(input in config.GAMEMODE_MATCH_MANIA):
		return utils.GAMEMODE_MANIA
	if(input in config.GAMEMODE_MATCH_TAIKO):
		return utils.GAMEMODE_TAIKO
	return GAMEMODE_STD # assume std if all else fails


def parse_user_data(username):
	pass