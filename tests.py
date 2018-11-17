import unittest
import db
import parser
import utils
import sys

class TestMethods(unittest.TestCase):
    def test_calcuate_accuracy_from_play(self):
        play =  {"count50": "0",
                "count100": "22",
                "count300": "680",
                "countmiss": "0",
                "countkatu": "17",
                "countgeki": "174"} # taken from my current top play
        self.assertEqual(utils.calc_acc(play, mode=0), "97.91")
        self.assertEqual(utils.calc_acc(play, mode=1), "98.43")
        self.assertEqual(utils.calc_acc(play, mode=2), "97.64") 
        self.assertEqual(utils.calc_acc(play, mode=3), "97.72") 

    def test_convert_api_rank_to_human_readable(self):
        self.assertEqual(utils.parse_play_rank("X"), "SS")
        self.assertEqual(utils.parse_play_rank("XH"), "SS")
        self.assertEqual(utils.parse_play_rank("SH"), "S")
        
    def test_convert_mod_integer_to_ordered_mod_string(self):
        self.assertEqual(utils.calc_mods(0), "Nomod")
        self.assertEqual(utils.calc_mods(4), "+TD")
        self.assertEqual(utils.calc_mods(192), "+DTRX")
        self.assertEqual(utils.calc_mods(4114), "+EZHRSO")
        self.assertEqual(utils.calc_mods(41), "+HDNFSD")

    def test_parse_title_data_from_title(self):
        self.assertEqual(parser.parse_title_data("[osu!std] tybug2 | blatant multiaccount"), ["0", "tybug2", ["multi", "true"], ["Blatant", "blatant"]])
        self.assertEqual(parser.parse_title_data("[osu!taiko]tybug2|spin hacker"), ["1", "tybug2", ["spinhack", "false"], ["Cheating", "cheating"]])
        self.assertEqual(parser.parse_title_data("[osu!m] not nathan"), ["3", "not nathan", ["other", "false"], ["Cheating", "cheating"]])
        self.assertEqual(parser.parse_title_data("cookiezi | being too good at the game"), None)
        self.assertEqual(parser.parse_title_data("[ sony ]"), None)
        self.assertEqual(parser.parse_title_data("[o!ctb][ sony ]"), ["2", "[ sony ]", ["other", "false"], ["Cheating", "cheating"]])
        self.assertEqual(parser.parse_title_data("[os!c] suki | cheating"), None)




# def run():
#     unittest.main(argv=sys.argv[1:]) 
#     # Remove all args from sys.argv. This seems like a hack but is actually relatively clean; when we call python main.py -t,
#     # we parse the t flag with argparse and then call unittest. Unittest also parses the args with argparse, 
#     # but doesn't understand the t flag. So we simply strip it before calling our tests

if __name__ == "__main__":
    unittest.main()