#!/usr/bin/env python
# -*- coding:utf-8 -*-


# logdog --upload-to-server -o result.txt f1.log f2.log
# logcat | logdog

import sys
import re
import json
from optparse import OptionParser
from collections import defaultdict
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
        tasts_list = self.config["taste"]
        for line in fobj:
            for tast in tasts_list:
                if re.search(tast["keystr_co"], line):
                    bone_text = []
                    bone_text.append(line)
                    # 找到所有续行
                    for xline in fobj:
                        if self._is_tag_line(xline, tast):
                            bone_text.append(xline)
                        else:
                            fobj.put(xline)
                            break

                    if not (callback is None):
                        callback(bone_text)
                    break

    def _is_tag_line(self, line, tast):
        '''
        是否是bone_text的续行

        如果tast.line_tag能够被line匹配，并且不能被所有tasts[x].keystr匹配，则返回True，否则返回False
        '''

        if not re.search(tast["line_tag"], line):
            return False

        tasts_list = self.config["taste"]
        for t in tasts_list:
            if re.search(t["keystr_co"], line):
                return False

        return True

    def put_queue(self, line):
        # print("put_queue")
        self.q.put(line)

    def detect_type(self, text):
        detector_list = self.config["logtype"]
        for x in detector_list:
            for line in text:
                if re.search(x["detector_co"], line):
                    return x

    def _parse_bone_time(self, text, logtype):
        for line in text:
            match = re.search(logtype["time_co"], line)
            if match:
                return match.group()

    def _parse_bone_text(self, text, logtype):
        new_text = "".join([re.sub(logtype["detector_co"], "", line) for line in text])

        match = re.search(logtype["item_repl_co"], new_text)
        if match:
            import array
            arr_text = array.array("u", new_text)
            spans = match.regs
            item_repl_co = logtype["item_repl_co"]
            groupdict = dict(zip(item_repl_co.groupindex.values(), item_repl_co.groupindex.keys()))
            for i in range(len(spans) - 1, 0, -1):
                arr_text[slice(*spans[i])] = array.array("u", "<" + groupdict[i] + ">")
            return arr_text.tounicode()
        return new_text

    def _parse_bone_item(self, text, logtype):
        match = re.search(logtype["item_co"], "".join(text))
        if match:
            return match.groupdict()

    def parse_bone(self, **kargs):
        while True:
            text = self.q.get()
            if text == "QUIT":
                break
            logtype = self.detect_type(text)
            # print(logtype)
            time_stamp = self._parse_bone_time(text, logtype)
            # print(time_stamp)
            notime_text = self._parse_bone_text(text, logtype)
            # print(notime_text)
            items = self._parse_bone_item(notime_text, logtype)
            # print(items)
            bone = Bone(notime_text, time_stamp, **items)
            self.counter.put(bone)
        return 0

    def quit_parse(self):
        self.q.put("QUIT")

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
    for x in config["taste"]:
        x["keystr_co"] = re.compile(x["keystr"])

    for x in config["logtype"]:
        x["detector_co"] = re.compile(x["detector"])
        x["time_co"] = re.compile(x["time"])
        x["item_co"] = re.compile(x["item"])
        x["item_repl_co"] = re.compile(x["item_repl"])

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
