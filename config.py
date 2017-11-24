#!/usr/bin/env python
# -*- coding:utf-8 -*-

config = {
    "server": {
        "ip": "192.168.1.3",
        "auth_key": ""
    },
    "logtype": [
        # 仅支持brief, threadtime, printable, time格式的logcat日志
        {
            # logcat -v printable
            # logcat -v threadtime
            # example:
            # 11-17 16:27:00.050  1519  1519 D SettingsInterface:  from settings cache , name = time_12_24 , value = 24
            # logcat -v usec
            # 11-17 16:27:00.050984  1519  1519 D SettingsInterfac  from settings cache , name = time_12_24 , value = 24
            "type": "logcat-threadtime",
            "detector": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+ +\d+ +\d+ [EWIDV] ",
            "time": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+",
            "item": r"AndroidRuntime: Process: (?P<proc_name>.*),.*\nAndroidRuntime: (?P<ex_name>.*?): (?P<ex_desc>.*)",
            "item_repl": r"AndroidRuntime: Process: .*,.PID: (?P<pid>\d+)"
        },
        # {
        #     # logcat -v time
        #     # example:
        #     #     11-17 16:27:00.050 D/SettingsInterface( 1519):  from settings cache , name = time_12_24 , value = 24
        #     "type": "logcat-time",
        #     "detector": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+ [EWIDV]/.+?\): ",
        #     "time": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+"
        # },
        # {
        #     # dmesg
        #     # example:
        #     #     [169533.232449]  (0)[239:bat_routine_thr][BAT_thread]Cable in, CHR_Type_num=1
        #     #     [169523.643622] -(8)[0:swapper/8]CPU8: update cpu_capacity 1024
        #     "type": "kernel",
        #     "detector": r"^\[[0-9\.]+\] [ -]?\(\d\)\[.+\]",
        #     "time": ""
        # }
    ],
    "taste": [
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