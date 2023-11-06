# -*- coding: utf-8 -*-
# @Time    : 2023/8/22 上午12:19
# @Author  : sudoskys
# @File    : rss.py
# @Software: PyCharm
import json
import socket

import feedparser
import html2text

socket.setdefaulttimeout(5)
feed_url = "https://ww"#"https://www.gcores.com/rss"  # "https://www.zhihu.com/rss"
res = feedparser.parse(feed_url)
print(res)
print(json.dumps(res, indent=4, ensure_ascii=False))
entries = res["entries"]
source = res["feed"]["title"]
_info = [
    {
        "title": entry["title"],
        "url": entry["link"],
        "id": entry["id"],
        "author": entry["author"],
        "summary": html2text.html2text(entry["summary"]),
    }
    for entry in entries
]
print(_info)
