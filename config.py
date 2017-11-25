#!/usr/bin/env python
# -*- coding:utf-8 -*-

config = {
    "server": {
        "ip": "192.168.1.3",
        "auth_key": ""
    },
    "logtype": {
        # 仅支持threadtime, printable, usec 格式的logcat日志
        # logcat -v printable
        # logcat -v threadtime
        # example:
        # 11-17 16:27:00.050  1519  1519 D SettingsInterface:  from settings cache , name = time_12_24 , value = 24
        # logcat -v usec
        # 11-17 16:27:00.050984  1519  1519 D SettingsInterfac  from settings cache , name = time_12_24 , value = 24
        "type": "logcat-threadtime",
        "charact": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+ +\d+ +\d+ [EWIDV] ",
        "time": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+",
        "item": r"AndroidRuntime: Process: (?P<proc_name>.*),.*\nAndroidRuntime: (?P<ex_name>.*?): (?P<ex_desc>.*)",
        "item_repl": r"AndroidRuntime: Process: .*,.PID: (?P<pid>\d+)"
    },
    "tastes": [
        {
            "type": "logcat",
            "keystr": r"FATAL EXCEPTION IN SYSTEM PROCESS",
            "line_tag": "AndroidRuntime:",
            "desc": "system_server进程崩溃"
        },
        {
            "type": "logcat",
            "keystr": r"pid:.*tid:.*name:.*>>>.*<<<",
            "line_tag": "I_DO_NOT_KNOW",
            "desc": "native crash"
        },
        {
            "type": "logcat",
            "keystr": r"FATAL EXCEPTION:",
            "line_tag": "AndroidRuntime:",
            "desc": "java crash"
        }

    ]
}