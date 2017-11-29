#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import unittest
from logdog import *


class WrapIterTest(unittest.TestCase):

    def setUp(self):
        with open("test.txt", "w") as f:
            text = ["line1\n", "line2\n", "line3\n"]
            f.write("".join(text))

    def tearDown(self):
        os.remove("test.txt")

    def test_wrap_file(self):
        with open("test.txt", "r") as f:
            fobj = WrapIter(f)
            self.assertEqual(next(fobj), "line1\n")
            fobj.put("newline")
            self.assertEqual(next(fobj), "newline")
            self.assertEqual(next(fobj), "line2\n")
            fobj.put("NEWLINE")
            self.assertEqual(next(fobj), "NEWLINE")
            self.assertEqual(next(fobj), "line3\n")

    def test_wrap_iter(self):
        it = WrapIter(iter([1, 2, 3]))
        self.assertEqual(next(it), 1)
        it.put("new")
        self.assertEqual(next(it), "new")
        it.put("new-2")
        self.assertEqual(next(it), "new-2")
        self.assertEqual(next(it), 2)
        self.assertEqual(next(it), 3)


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


class BoneTest(unittest.TestCase):

    def test_bone(self):
        # bone.text只要一样，就表示bone是相等的，即使其他字段不一样
        bone1_1 = Bone("text1", "01-01 00:00:00.001", "proc_name-1", "reason-1", "reason_detail-1")
        bone1_2 = Bone("text1", "01-01 00:00:00.002", "proc_name-2", "reason-2", "reason_detail-2")
        self.assertEqual(bone1_1, bone1_2)

        # bone.text只要不一样，就表示bone是不相等的，即使其他字段完全一样
        bone2_1 = Bone("text2-1", "01-01 00:00:00.001", "proc_name", "reason", "reason_detail")
        bone2_2 = Bone("text2-2", "01-01 00:00:00.001", "proc_name", "reason", "reason_detail")
        self.assertNotEqual(bone2_1, bone2_2)


if __name__ == "__main__":
    unittest.main()
