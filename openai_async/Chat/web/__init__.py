# -*- coding: utf-8 -*-
# @Time    : 12/16/22 1:37 PM
# @FileName: __init__.py.py
# @Software: PyCharm
# @Github    ：sudoskys
import gzip
import random
import httpx
from urllib.parse import urlparse

from openai_async.utils.Talk import Talk

info_cache = {}
client = httpx.Client()


class webEnhance(object):
    def __init__(self, server: list):
        self._server = None
        if server:
            self._server = random.choice(server)

    @staticmethod
    def deal_res(query, res):
        import re
        stop_sentence = ["下面就让我们",
                         "小编", "一起来看一下", "小伙伴们",
                         "究竟是什么意思", "看影片", "看人次", "？", "?", "是什么", "什么意思", "意思介绍", " › ",
                         "游侠", "_哔哩哔哩_bilibili", "为您提供", "今日推荐", "線上看", "线上看", "知乎"]
        skip = False
        for ir in stop_sentence:
            if ir in res:
                skip = True
        pas = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        _link = re.findall(pas, res)
        if _link:
            for i in _link:
                res = res.replace(i, "")
        _link = re.findall("(?:[\w-]+\.)+[\w-]+", res)
        if _link:
            if len("".join(_link)) / len(res) > 0.7:
                skip = True
            for i in _link:
                res = res.replace(i, "")
        if skip:
            return ""
        # 处理数据
        sentence = res.strip(".").strip("…").replace('\xa0', '').replace('    ', '').replace("\r", '')
        sentence = sentence.replace("，", ",").replace("。", ".")
        if 18 < len(sentence):
            return sentence
        else:
            return ""

    @staticmethod
    def get_tld(url):
        parsed_url = urlparse(url)
        return parsed_url.netloc

    def req_server(self,
                   query: str = "KKSK 是什么意思？"
                   ):
        if self._server:
            _url = self._server.format(query)
        else:
            return
        from bs4 import BeautifulSoup
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, defalte",
            "Connection": "keep-alive",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Host": f"{self.get_tld(self._server)}",
            "Referer": f"https://www.{self.get_tld(self._server)}/",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0"
        }
        html = client.get(_url, headers=headers, follow_redirects=True, timeout=10)
        htmltext = html.text
        # 匹配
        sret = {}
        if "html" in htmltext:
            rs = BeautifulSoup(htmltext, "lxml")
            # print(rs.text)
            if "goog" in self._server:
                target = ["html", rs.select("div > span")]
            else:
                target = ["html", rs.select("div")]
        else:
            target = ["text", htmltext.split("\n")]
        if target[0] == "html":
            for i in target[1]:
                if i.parent.select("a[href]"):
                    continue
                res = i.parent.text
                cr = self.deal_res(query=query, res=res)
                if cr:
                    sret[cr] = 0
        else:
            for i in target[1]:
                cr = self.deal_res(query=query, res=i)
                if cr:
                    sret[cr] = 0
        return list(sret.keys())

    def get_content(self, prompt: str):
        global info_cache
        if info_cache.get(prompt):
            return info_cache.get(prompt)
        _returner = []
        _list = self.req_server(prompt)
        if not _list:
            return []
        # list 互相匹配
        for ir in range(0, len(_list), 2):
            _pre = _list[ir]
            _afe = _list[ir]
            _deal = _list
            sim = Talk.cosion_sismilarity(pre=_pre, aft=_afe)
            if sim < 0.3:
                _list.remove(_afe)
        # 关键词算法匹配
        _key = Talk.tfidf_keywords(prompt, topK=5)
        for i in _list:
            for ir in _key:
                if ir in i:
                    _returner.append(i)
        info_cache[prompt] = _returner
        return _returner


if __name__ == '__main__':
    re = webEnhance(server=["https://www.exp.com?ie=utf8&query={}"]).get_content(prompt="介绍孤独摇滚")
    print(re)
