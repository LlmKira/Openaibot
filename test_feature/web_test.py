# -*- coding: utf-8 -*-
# @Time    : 12/16/22 2:54 PM
# @FileName: .py
# @Software: PyCharm
# @Github    ：sudoskys
# !pip3 install newspaper3k
"""
import nltk

nltk.download('punkt')
from newspaper import Config, Article, Source

config = Config()
config.memoize_articles = True
config.fetch_images = False
config.keep_article_html = False


url = "https://www.google.com/search?q=2022世界杯什么时候举行"
url = "https://duckduckgo.com/?t=ffab&q=awsl是什么意思&ia=web"
url = "https://www.google.com/search?q=孤独摇滚是什么动漫&oq=孤独摇滚是什么动漫"
url = 'https://www.bing.com/search?q=孤独摇滚是什么动漫'
article = Article(url)
article.download()
# url="https://jikipedia.com/search?phrase=丁真珍珠"
article.parse()
# print('html:', article.html)
print(article.article_html)
# print('authors:', article.authors)
print('title:', article.title)
# print('date:', article.publish_date)
print('text:', article.text)
# print('top image:', article.top_image)
# print('movies:', article.movies)
article.nlp()
print('keywords:', article.keywords)
print('summary:', article.summary)

"""


def deal_res(query, res):
    import re
    stop_sentence = ["下面就让我们",
                     "小编", "一起来看一下", "小伙伴们",
                     "究竟是什么意思", "看影片", "看人次", "？", "?", "是什么", "什么意思", "意思介绍", " › ",
                     "游侠", "_哔哩哔哩_bilibili",
                     "为您提供", "今日推荐", "線上看", "线上看",
                     "TikTok", "時間長度", "發布時間", "时间长度", "发布时间"]
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
    sentence = res.strip(".").strip("\xa0").strip("…")
    sentence = sentence.replace("，", ",").replace("。", ".")
    if 20 < len(sentence):
        return sentence
    else:
        return ""


def get_content(query: str = "KKSK 是什么意思？",
                server: str = None):
    import httpx
    from bs4 import BeautifulSoup
    headers = {
        # "Accept": "image/gif, image/jpeg, image/pjpeg, application/x-ms-application, application/xaml+xml, application/x-ms-xbap, */*",
        # "Accept-Encoding": "gzip, deflate",
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; Tablet PC 2.0; wbx 1.0.0; wbxapp 1.0.0; Zoom 3.6.0)",
        # "X-Amzn-Trace-Id": "Root=1-628b672d-4d6de7f34d15a77960784504"
    }
    if not server:
        return
    with httpx.Client() as client:
        html = client.get(server.format(query), headers=headers, follow_redirects=False)
    rs = BeautifulSoup(html.text, "lxml")
    # print(rs.text)
    # 匹配
    sret = {}
    if "goog" in server:
        target = rs.select("div > span")
    else:
        target = rs.select("div")
    if target:
        for i in target:
            if i.parent.select("a[href]"):
                continue
            res = i.parent.text
            cr = deal_res(query=query, res=res)
            if cr:
                sret[cr] = 0
    return list(sret.keys())


# ONLY FOR TEST! DONT USE THESE LINK ,Commercial use at your own risk
"https://www.bing.com/search?q={}&form=QBLH"
"https://www.google.com/search?client=edge&q={}"
s = get_content(server="https://www.google.com/search?client=edge&q={}")
print(s)

"""
['2020年1月29日 · Cxk就是蔡徐坤,中国内地男歌手、演员、音乐制作人,98年生,当红小鲜肉. · Cxk没有多深的梗,只是简单的名字拼音开头. · 但,真粉丝会直呼其名,或者使用', '2019年12月23日 · 字面意义为“小心点,你（因为你的行为）要收到律师函了”.目前多用于调侃某些在维权方面极端敏感的公众人物或团体. 该词的流行主要因为明星蔡徐坤不满B站', '2022年2月16日 · 最近,网红在痞幼发了一个开团了,导致蔡徐坤的黑粉们疯狂晒cxk的黑图,从而导致大量cxk的粉丝来骂痞幼,事后痞幼迅速出来道歉说自己说的开团了是游戏']
"""

"""
['ここすき,这里意为喜欢,通常被用在弹幕之中,是对视频某一片段表达赞赏用的. 似乎只有在中国才会被缩写为kksk（ここkokoすきsuki）.', '2022年3月16日 · ここすき,是發源於niconico彈幕的用語,也會被略寫為kksk. 解釋. ここすき,意為這裡喜歡,通常被用在彈幕之中,是對視頻某一片段表達讚賞用的.', '2021年9月3日 · 原來「kksk」是日語「我喜歡這裡」的羅馬音「Koko-suki」的縮寫,發源於日本彈幕網站Niconico,觀眾看到喜歡的視頻內容時,會發送「kksk」的彈幕來表達.', '2021年8月4日 · kksk表示很喜欢,喜欢某一个片段、某一个事物等等称赞. kksk含义. kksk最开始是在MAD视频的弹幕中,表示自己很喜欢这一段,后来', '2021年11月25日 · kksk在网络中并不是“看看谁快”的中文拼音首字母的缩写,而是来自日本的一个二次元用语,即日语“ここ好き”的罗马音“ko ko SU KI”的缩写,意思是“喜欢']
"""
