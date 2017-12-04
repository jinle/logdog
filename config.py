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
        "charact": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+ +\d+ +\d+ [FEWIDV] ",
        "time": r"^\d\d-\d\d \d\d:\d\d:\d\d\.\d+"
    },
    "tastes": [
        {
            "name": "system-crash",
            "begin_tag": r"FATAL EXCEPTION IN SYSTEM PROCESS:",
            "key_tag": r"FATAL EXCEPTION IN SYSTEM PROCESS:",
            "line_tag": [r"AndroidRuntime:"],
            "item": {
                "proc_name": "system_server",
                "re": [
                    r"FATAL EXCEPTION IN SYSTEM PROCESS:.*\nAndroidRuntime: (?P<ex_name>.*?): (?P<ex_desc>.*)"
                ]
            },
            "item_repl": [r"I_DO_NOT_KNOW"]
        },
        {
            "name": "native-crash",
            "begin_tag": r"(\*\*\* ){15}\*\*\*",
            "key_tag": r"pid:.*tid:.*name:.*>>>.*<<<",
            "line_tag": [r"DEBUG   :", r"AEE/AED :"],
            "item": {
                "re": [
                    r"pid:.*tid:.*name:.*>>> (?P<proc_name>.*) <<<",
                    r".* signal .*?\((?P<ex_name>\w+)\), code .*?\((?P<ex_desc>.+)\)"
                ]
            },
            "item_repl": [
                r"pid: (?P<pid>\d+), tid: (?P<tid>\d+), name:.*",
                r"signal .*, code .*, fault addr (?P<addr>\w+)",
                r"Build fingerprint: '(?P<fingerprint>.*)'",
                r"Tombstone written to: .*/tombstone_(?P<id>\d\d)"
            ],
            "method_repl": "native_crash_repl"
        },
        {
            "name": "app-crash",
            "begin_tag": r"FATAL EXCEPTION:",
            "key_tag": r"FATAL EXCEPTION:",
            "line_tag": ["AndroidRuntime:"],
            "item": {
                "re": [
                    r"AndroidRuntime: Process: (?P<proc_name>.*),.*\nAndroidRuntime: (?P<ex_name>.*?): (?P<ex_desc>.*)"
                ]
            },
            "item_repl": [r"AndroidRuntime: Process: .*,.PID: (?P<pid>\d+)"]
        },
        {
            "name": "app-anr",
            "begin_tag": r"ActivityManager: ANR in ",
            "key_tag": r"ActivityManager: ANR in ",
            "line_tag": ["ActivityManager:"],
            "end_tag": r"ActivityManager: Load: [\d.]+ / [\d.]+ / [\d.]+",
            "item": {
                "ex_desc": None,
                "re": [
                    r"ActivityManager: ANR in (?P<proc_name>\S*)( .*)?",
                    r"ActivityManager: Reason: (?P<ex_name>Input .*) \(.*\)",
                    r"ActivityManager: Reason: (?P<ex_name>Broadcast .*)",
                    r"ActivityManager: Reason: (?P<ex_name>executing .*)"
                ]
            },
            "item_repl": [
                r"ActivityManager: PID: (?P<pid>\d+)",
                r"ActivityManager: Reason: Input .*\((?P<reason_detail>.*)\)",
            ]
        }
    ]
}
