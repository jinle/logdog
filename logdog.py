#!/usr/bin/env python
# -*- coding:utf-8 -*-


# logdog --upload-to-server -o result.txt f1.log f2.log
# logcat | logdog

import sys
import re
import json
import array
from optparse import OptionParser
from collections import defaultdict
from operator import methodcaller
from queue import Queue
from threading import Thread

import config


class WrapFile:

    def __init__(self, fobj):
        self.fobj = fobj
        self.line = None

    def put(self, line):
        self.line = line

    def __iter__(self):
        return self

    def __next__(self):

        if self.line is None:
            return self.fobj.__next__()
        else:
            x, self.line = self.line, None
            return x


class Counter:

    def __init__(self):
        self.dict = defaultdict(list)

    def put(self, obj):
        self.dict[obj].append(obj.time_stamp)

    def result(self):
        return {key: len(set(value)) for key, value in self.dict.items()}


class LogDog:

    def __init__(self, config):
        self.q = Queue()
        self.config = config
        self.counter = Counter()

        # print(json.dumps(self.config, indent=4, default=lambda x: repr(x)))

    def search(self, fobj, callback=None):
        tastes = self.config["tastes"]
        for line in fobj:
            for t in tastes:
                if re.search(t["begin_tag_co"], line):
                    bone_text = []
                    bone_text.append(line)
                    # 找到所有续行
                    for xline in fobj:
                        if self._is_tag_line(xline, t):
                            bone_text.append(xline)
                        else:
                            fobj.put(xline)
                            break

                    if not (callback is None):
                        callback((bone_text, t))
                    break

    def _is_tag_line(self, line, tast):
        '''
        是否是bone_text的续行

        如果tast.line_tag能够被line匹配，并且不能被所有tasts[x].line_tag匹配，则返回True，否则返回False
        '''
        line_tag = None
        for tag in tast["line_tag"]:
            if re.search(tag, line):
                line_tag = tag
        if line_tag is None:
            return False

        tastes = self.config["tastes"]
        for t in tastes:
            if re.search(t["begin_tag_co"], line):
                return False

        return True

    def put_queue(self, bone_info):
        # print("put_queue")
        self.q.put(bone_info)

    def detect_type(self, text):
        logtype = self.config["logtype"]
        for line in text:
            if re.search(logtype["charact_co"], line):
                return logtype

    def _parse_bone_time(self, text, logtype):
        for line in text:
            match = re.search(logtype["time_co"], line)
            if match:
                return match.group()

    def _remove_time_stamp(self, text, logtype):
        new_text = [re.sub(logtype["charact_co"], "", line) for line in text]
        return "".join(new_text)

    def _remove_text_chip(self, text, taste):
        for x in taste["item_repl_co"]:
            match = re.search(x, text)
            if match:
                arr_text = array.array("u", text)
                spans = match.regs
                groupdict = dict(zip(x.groupindex.values(), x.groupindex.keys()))
                for i in range(len(spans) - 1, 0, -1):
                    arr_text[slice(*spans[i])] = array.array("u", "<" + groupdict[i] + ">")
                text = arr_text.tounicode()
        return text

    def _parse_bone_item(self, text, taste):
        match = re.search(taste["item_co"], "".join(text))
        if match:
            return match.groupdict()

    def native_crash_repl(self, text, taste):
        text_list = text.split("\n")
        start_co = re.compile(r"signal.*, code.*, fault addr")
        end_co = re.compile(r"backtrace:$")
        start = 0
        end = 0
        for no, line in enumerate(text_list):
            if start == 0 and re.search(start_co, line):
                start = no
            if end == 0 and re.search(end_co, line):
                end = no
            if start != 0 and end != 0:
                break
        for i in range(end - 1, start, -1):
            if text_list[i].find("    ") > 0:
                del text_list[i]

        return "\n".join(text_list)

    def parse_bone(self, **kargs):
        while True:
            bone_info = self.q.get()
            text = bone_info[0]
            taste = bone_info[1]

            if text == "QUIT":
                break

            logtype = self.detect_type(text)
            # print(logtype)
            time_stamp = self._parse_bone_time(text, logtype)
            # print(time_stamp)
            notime_text = self._remove_time_stamp(text, logtype)
            # print(notime_text)
            new_text = self._remove_text_chip(notime_text, taste)
            # print(new_text)
            if "method_repl" in taste:
                if getattr(self, taste["method_repl"]):
                    new_text = methodcaller("native_crash_repl", new_text, taste)(self)

            items = self._parse_bone_item(new_text, taste)
            # print(items)
            bone = Bone(new_text, time_stamp, **items)
            self.counter.put(bone)
        return 0

    def quit_parse(self):
        self.q.put(("QUIT", None))

    def print_result(self, fobj):
        for key, value in self.counter.result().items():
            print("=" * 100, file=fobj)
            print("count =", value, "proc_name =", key.proc_name, "exception =", key.ex_name, file=fobj)
            print("-" * 100, file=fobj)
            print(key.text, file=fobj)


class Bone(object):

    def __init__(self, text, time_stamp, proc_name, ex_name, ex_desc):
        self.text = text
        self.time_stamp = time_stamp
        self.proc_name = proc_name
        self.ex_name = ex_name
        self.ex_desc = ex_desc

    def __repr__(self):
        return 'Bone(proc_name={0.proc_name!r}, ex_name={0.ex_name!r})'.format(self)

    def __hash__(self):
        return hash(self.text)

    def __eq__(self, other):
        return self.text == other.text


def init_config(config):

    logtype = config["logtype"]
    logtype["charact_co"] = re.compile(logtype["charact"])
    logtype["time_co"] = re.compile(logtype["time"])

    tastes = config["tastes"]
    for t in tastes:
        t["begin_tag_co"] = re.compile(t["begin_tag"])
        t["item_co"] = re.compile(t["item"])
        t["item_repl_co"] = [re.compile(x) for x in t["item_repl"]]
    return config


def parse_args():
    parser = OptionParser(usage="%prog [optinos] [logcat.txt ...]")
    parser.add_option("-u", "--upload-result",
                      dest="upload_result",
                      action="store_true",
                      default=False,
                      help="Upload result to server after scan over"
                      )
    parser.add_option("-o", "--outfile",
                      action="store",
                      dest="outfile",
                      help="Write result to OUTFILE, default is stdout"
                      )
    parser.add_option("-V", "--version",
                      action="store_true",
                      default=False,
                      help="Print the version"
                      )
    return parser.parse_args()


def main():
    options, args = parse_args()
    if options.version:
        print("0.1.0")
        exit(0)

    conf = init_config(config.config)

    outfobj = sys.stdout
    try:
        if not (options.outfile is None):
            outfobj = open(options.outfile, "wt")
    except Exception as ex:
        print(ex, file=sys.stderr)
        exit(1)

    logdog = LogDog(conf)
    proc = Thread(target=logdog.parse_bone)
    proc.start()

    try:
        if len(args) == 0:
            logdog.search(WrapFile(sys.stdin), logdog.put_queue)
        else:
            for fname in args:
                with open(fname, "rt", encoding="utf-8") as f:
                    logdog.search(WrapFile(f), logdog.put_queue)
    except Exception as ex:
        print(ex, file=sys.stderr)

    logdog.quit_parse()
    proc.join()

    logdog.print_result(outfobj)


if __name__ == "__main__":
    main()
