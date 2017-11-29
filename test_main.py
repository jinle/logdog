#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import unittest
from logdog import *


class WrapFileTest(unittest.TestCase):

    def setUp(self):
        with open("test.txt", "w") as f:
            text = ["line1\n", "line2\n", "line3\n"]
            f.write("".join(text))

    def tearDown(self):
        os.remove("test.txt")

    def test_wrap_file(self):
        with open("test.txt", "r") as f:
            fobj = WrapFile(f)
            self.assertEqual(next(fobj), "line1\n")
            fobj.put("newline")
            self.assertEqual(next(fobj), "newline")
            self.assertEqual(next(fobj), "line2\n")
            fobj.put("NEWLINE")
            self.assertEqual(next(fobj), "NEWLINE")
            self.assertEqual(next(fobj), "line3\n")


class CounterTest(unittest.TestCase):

    def test_counter(self):
        counter = Counter()
        bone1 = Bone("text1", "01-01 00:00:00.000", "proc_name", "reason", "reason_detail")
        bone2_1 = Bone("text2", "01-01 00:00:00.001", "proc_name", "reason", "reason_detail")
        bone2_2 = Bone("text2", "01-01 00:00:00.002", "proc_name", "reason", "reason_detail")

        counter.put(bone1)
        counter.put(bone2_1)
        counter.put(bone2_2)
        result = counter.result()

        self.assertEqual(len(result), 2)

        self.assertTrue(result[bone1] == 1)
        self.assertTrue(result[bone2_1] == 2)
        self.assertTrue(result[bone2_1] == 2)


if __name__ == "__main__":
    unittest.main()
