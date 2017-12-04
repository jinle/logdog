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


def sessin(*files):
    def deco(func):
        def wrap(self, *args, **kwargs):
            self.logdog.counter.clear()
            self.logdog.start()
            for f in files:
                self.logdog.search(f)
            self.logdog.stop()
            func(self, *args, **kwargs)
        return wrap
    return deco


class LogDogTest(unittest.TestCase):

    def setUp(self):
        self.logdog = LogDog()
        self.logdog.load_config()

    def tearDown(self):
        pass

    @sessin("extras/log/app-anr-mtk-1.txt")
    def test_app_anr_mtk_1(self):
        result = self.logdog.counter.result()
        self.assertEqual(len(result), 1)
        k, v = list(result.items())[0]
        self.assertEqual(k.proc_name, "com.qiku.eyemode")
        self.assertEqual(k.ex_name, "Broadcast of Intent { act=android.intent.action.SCREEN_OFF flg=0x50000010 }")
        self.assertEqual(v, 1)

    @sessin("extras/log/app-anr-mtk-2.txt")
    def test_app_anr_mtk_2(self):
        result = self.logdog.counter.result()
        self.assertEqual(len(result), 1)
        k, v = list(result.items())[0]
        self.assertEqual(k.proc_name, "com.google.android.gms.persistent")
        self.assertEqual(k.ex_name, "executing service com.google.android.gms/com.google.android.location.reporting.service.DispatchingService")
        self.assertEqual(v, 1)

    @sessin("extras/log/app-anr-google-1.txt")
    def test_app_anr_google_1(self):
        result = self.logdog.counter.result()
        self.assertEqual(len(result), 1)
        k, v = list(result.items())[0]
        self.assertEqual(k.proc_name, "com.android.development")
        self.assertEqual(k.ex_name, "Input dispatching timed out")
        self.assertEqual(v, 1)

    @sessin("extras/log/app-anr-mtk-2.txt", "extras/log/app-anr-google-1.txt", "extras/log/app-anr-google-1.txt")
    def test_app_anr_comb_1(self):
        result = self.logdog.counter.result()
        bones = result.keys()
        counters = list(result.values())
        self.assertEqual(len(result), 2)
        self.assertIn("com.google.android.gms.persistent", [x.proc_name for x in bones])
        self.assertIn("com.android.development", [x.proc_name for x in bones])
        self.assertEqual(counters[0], 1)
        self.assertEqual(counters[1], 1)

    @sessin("extras/log/app-jvm-crash-google-1.txt")
    def test_app_jvm_crash_google_1(self):
        result = self.logdog.counter.result()
        self.assertEqual(len(result), 1)
        k, v = list(result.items())[0]
        self.assertEqual(k.proc_name, "com.android.development")
        self.assertEqual(k.ex_name, "com.android.development.BadBehaviorActivity$BadBehaviorException")
        self.assertEqual(v, 1)

    @sessin("extras/log/app-jvm-crash-qcom-1.txt")
    def test_app_jvm_crash_qcom_1(self):
        result = self.logdog.counter.result()
        self.assertEqual(len(result), 1)
        k, v = list(result.items())[0]
        self.assertEqual(k.proc_name, "com.example.company.test_exception")
        self.assertEqual(k.ex_name, "java.lang.NullPointerException")
        self.assertEqual(v, 1)

    @sessin("extras/log/app-jvm-crash-qcom-2.txt")
    def test_app_jvm_crash_qcom_2(self):
        result = self.logdog.counter.result()
        self.assertEqual(len(result), 1)
        k, v = list(result.items())[0]
        self.assertEqual(k.proc_name, "com.example.company.test_exception")
        self.assertEqual(k.ex_name, "java.lang.RuntimeException")
        self.assertEqual(v, 3)

    @sessin("extras/log/app-jvm-crash-qcom-3.txt")
    def test_app_jvm_crash_qcom_3(self):
        result = self.logdog.counter.result()
        self.assertEqual(len(result), 1)
        k, v = list(result.items())[0]
        self.assertEqual(k.proc_name, "com.qiku.logsystem")
        self.assertEqual(k.ex_name, "java.lang.RuntimeException")
        self.assertEqual(v, 1)


if __name__ == "__main__":
    unittest.main()
