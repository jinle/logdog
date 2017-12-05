#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

import sys
import re
import array
from optparse import OptionParser
from collections import defaultdict
from operator import methodcaller
from threading import Thread
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from codecs import open


class WrapIter:
    """对迭代器进行包装，使迭代器支恢复操作

    在本项目中，每次从file对象中获取一行文本，以判定此行文本与之前的文本是否属于同一个异常信息．
    当读取到一行文本不属于之前的异常信息时，我们希望把这行文本再恢复到迭代器中，以便下次扫描时，
    可以重新读取完整的文本．
    """

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

    def next(self):
        '''兼容Python2：实现迭代器'''
        if self.line is None:
            return next(self.fobj)
        else:
            x, self.line = self.line, None
            return x


class Counter:
    '''对扫描到的异常信息(Bone对象)进行数量统计

    如果一个异常在日志中出现N次，那么其异常信息是相同的，但每次的时间戳是不一样的，其统计次数为N．
    如果由于某中原因出现了异常信息及时间戳完全一样的bone（日志重复），则只应该统计1次．
    所有异常文本相同的bone对应一个列表，列表中保存了这些bone的时间戳，去除重复的时间戳后的个数，
    即为统计结果．
    '''

    def __init__(self):
        self.dict = defaultdict(list)

    def put(self, obj):
        self.dict[obj].append(obj.time_stamp)

    def clear(self):
        self.dict = defaultdict(list)

    def result(self):
        return {key: len(set(value)) for key, value in self.dict.items()}


class LogDog:
    """对日志进行扫描，根据taste在日志中寻找bone，并输出统计结果

    由两个线程构成，搜索线程（主线程）和分析统计线程．
    搜索线程根据taste提供的特征进行日志中搜索taste，将搜索到的异常信放入queue中
    分析统计线程从queue中取得异常信息，进行更为精确的匹配和统计．
    """

    def __init__(self):
        self.q = Queue()
        self.counter = Counter()

        # import json
        # print(json.dumps(self.config, indent=4, default=lambda x: repr(x)))

    def load_config(self):

        from config import config

        logtype = config["logtype"]
        logtype["charact_co"] = re.compile(logtype["charact"])
        logtype["time_co"] = re.compile(logtype["time"])

        tastes = config["tastes"]
        for t in tastes:
            t["begin_tag_co"] = re.compile(t["begin_tag"])
            if "end_tag" in t:
                t["end_tag_co"] = re.compile(t["end_tag"])
            t["item"]["re_co"] = [re.compile(x) for x in t["item"]["re"]]
            t["item_repl_co"] = [re.compile(x) for x in t["item_repl"]]

        self.config = config
        return True

    def start(self):
        # 启动分析统计线程
        self.thr = Thread(target=self.parse_bone)
        self.thr.start()

    def stop(self):
        # 日志文件搜索结束,请求分析统计线程退出
        self.q.put(("QUIT", None))
        self.thr.join()

    def _search(self, fobj, callback):
        tastes = self.config["tastes"]
        for line in fobj:
            line = line.replace("\r\n", "\n")
            for t in tastes:
                if re.search(t["begin_tag_co"], line):
                    bone_text = []
                    bone_text.append(line)
                    # 找到所有续行
                    for xline in fobj:
                        xline = xline.replace("\r\n", "\n")
                        if self._is_tag_line(xline, t):
                            bone_text.append(xline)
                        else:
                            fobj.put(xline)
                            break

                    if not (callback is None):
                        callback((bone_text, t))
                    break

    def search(self, fobj):
        callback = self.put_queue

        if isinstance(fobj, str):
            try:
                with open(fobj, "r", encoding="utf-8") as f:
                    self._search(WrapIter(f), callback)
            except Exception as ex:
                print(ex, file=sys.stderr)
        else:
            self._search(WrapIter(fobj), callback)

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

        if "end_tag_co" in tast and re.search(tast["end_tag_co"], line):
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
                    arr_text[slice(*spans[i])] = array.array("u", u"<" + groupdict[i] + u">")
                text = arr_text.tounicode()
        return text

    def _parse_bone_item(self, text, taste):
        item = taste["item"]
        result = {k: v for k, v in item.items() if not k in ["re", "re_co"]}

        for x in item["re_co"]:
            match = re.search(x, text)
            if match:
                result.update(match.groupdict())
        return result

    def native_crash_repl(self, text, taste):
        """处理native-crash日志中出现的内存地址等随机数字

        目前处理方式是删除这些行
        TODO(jinle): 将内存地址这样的随机数字替换为<addr>
        """
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
            bone = Bone(new_text, time_stamp, **items)
            self.counter.put(bone)
        return 0

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

    def __ne__(self, other):
        return self.text != other.text


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

    outfobj = sys.stdout
    try:
        if not (options.outfile is None):
            outfobj = open(options.outfile, mode="w", encoding="utf-8")
    except Exception as ex:
        print(ex, file=sys.stderr)
        exit(1)

    logdog = LogDog()
    logdog.load_config()
    logdog.start()

    if len(args) == 0:
        logdog.search(sys.stdin)
    else:
        for fname in args:
            logdog.search(fname)

    logdog.stop()
    # 输出结果
    logdog.print_result(outfobj)


if __name__ == "__main__":
    main()
