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
        self.assertEqual(utils.calc_acc(play, mode="0"), "97.91")
        self.assertEqual(utils.calc_acc(play, mode="1"), "97.91") # TODO
        self.assertEqual(utils.calc_acc(play, mode="2"), "97.91") # TODO
        self.assertEqual(utils.calc_acc(play, mode="3"), "97.91") # TODO

    def test_convert_api_rank_to_human_readable(self):
        self.assertEqual(utils.parse_play_rank("X"), "SS")
        self.assertEqual(utils.parse_play_rank("XH"), "SS")
        self.assertEqual(utils.parse_play_rank("SH"), "S")

# def run():
#     unittest.main(argv=sys.argv[1:]) 
#     # Remove all args from sys.argv. This seems like a hack but is actually relatively clean; when we call python main.py -t,
#     # we parse the t flag with argparse and then call unittest. Unittest also parses the args with argparse, 
#     # but doesn't understand the t flag. So we simply strip it before calling our tests

if __name__ == '__main__':
    unittest.main()