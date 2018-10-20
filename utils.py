from config import *

def calc_acc(play, mode):
    """
    Calculates the accuracy of the given play based on the forumla (currently) in https://osu.ppy.sh/help/wiki/Accuracy. 
    Accepts data in the format of a play from get_user_best, get_user_recent, get_scores (for a specific beatmap) or individual plays from get_match
    """

    count0 = int(play["countmiss"])
    count50 = int(play["count50"])
    count100 = int(play["count100"])
    count300 = int(play["count300"])
    countkatu = int(play["countkatu"])
    countgeki = int(play["countgeki"])

    if(mode == "0"): # std
        acc = (50*count50+ 100*count100 + 300*count300) / (300 * (count0 + count50 + count100 + count300))
    elif(mode == "1"): # taiko
        acc = (0.5*count100 + count300) / (count0 + count100 + count300)
    elif(mode == "2"): # ctb
        acc = (count50 + count100 + count300) / (count0 + countkatu + count50 + count100 + count300)
    elif(mode == "3"): # mania
        acc = (50*count50 + 100*count100 + 200*countkatu + 300*(count300 + countgeki)) / (300 * (count0 + count50 + count100 + countkatu + count300 + countgeki))

    return acc * 100 # convert to percent



def calc_mods(mods_int):
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


def parse_play_rank(rank):
    ranks = {"X": "SS", "XH" : "SS", "SH" : "S"}
    return ranks[rank] if rank in ranks else rank