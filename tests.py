import unittest

import db
import parser
import utils
import main


class TestMethods(unittest.TestCase):
    def calcuate_accuracy_from_play(self):
        play =  ["count50": "0",
                "count100": "22",
                "count300": "680",
                "countmiss": "0",
                "countkatu": "17",
                "countgeki": "174"] # taken from my current top play
        self.assertEqual(utils.calc_acc(play, mode=0), "97.91")
        self.assertEqual(utils.calc_acc(play, mode=1), "97.91") # TODO
        self.assertEqual(utils.calc_acc(play, mode=2), "97.91")
        self.assertEqual(utils.calc_acc(play, mode=3), "97.91")

    def convert_api_rank_to_human_readable(self):
        self.assertEqual(utils.parse_play_rank("X"), "SS")
        self.assertEqual(utils.parse_play_rank("XH"), "SS")
        self.assertEqual(utils.parse_play_rank("SH"), "S")

if __name__ == '__main__':
    unittest.main()