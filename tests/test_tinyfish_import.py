import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tinyfish_import  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "tinyfish_2026-10-14.html")


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.rows = tinyfish_import.parse(open(FIXTURE, encoding="utf-8").read())

    def by(self, op, prize):
        return [r["4d_number"] for r in self.rows if r["operator"] == op and r["prize"] == prize]

    def test_only_the_three_operators(self):
        self.assertEqual({r["operator"] for r in self.rows}, {"Magnum", "Sports Toto", "Da Ma Cai"})
        self.assertEqual({r["date"] for r in self.rows}, {"2026-10-14"})
        self.assertEqual({r["day"] for r in self.rows}, {"Wed"})

    def test_top_three(self):
        self.assertEqual(self.by("Magnum", "1st") + self.by("Magnum", "2nd") + self.by("Magnum", "3rd"),
                         ["3872", "3175", "1274"])
        self.assertEqual(self.by("Sports Toto", "1st"), ["9332"])
        self.assertEqual(self.by("Da Ma Cai", "3rd"), ["6516"])

    def test_special_skips_dashes(self):
        self.assertEqual(self.by("Magnum", "Special"),
                         ["9432", "0504", "7685", "3683", "0877", "0164", "8480", "5730", "9152", "1613"])
        self.assertEqual(len(self.by("Sports Toto", "Special")), 10)
        self.assertEqual(len(self.by("Da Ma Cai", "Special")), 10)

    def test_consolation(self):
        self.assertEqual(self.by("Magnum", "Consolation"),
                         ["4661", "2995", "3368", "3934", "2300", "3039", "9686", "6307", "7484", "4904"])
        self.assertEqual(self.by("Da Ma Cai", "Consolation")[-1], "4482")


if __name__ == "__main__":
    unittest.main()
