# -*- coding: utf-8 -*-
# @Time    : 12/7/22 10:14 PM
# @FileName: nlp.py
# @Software: PyCharm
# @Github    ：sudoskys
from case_server import CutParent
from openai_async.Chat import Chatbot
import nltk

nltk.download('punkt')
nltk.download('stopwords')
"""
    - '/home/nano/nltk_data'
    - '/home/nano/miniconda3/envs/LoveBot/nltk_data'
    - '/home/nano/miniconda3/envs/LoveBot/share/nltk_data'
    - '/home/nano/miniconda3/envs/LoveBot/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
"""
if __name__ == "__main__":
    import timeit
    def test_summary():
        en_word = """
        A wiki enables communities of editors and contributors to write documents collaboratively. All that people require to contribute is a computer, Internet access, a web browser, and a basic understanding of a simple markup language (e.g. MediaWiki markup language). A single page in a wiki website is referred to as a "wiki page", while the entire collection of pages, which are usually well-interconnected by hyperlinks, is "the wiki". A wiki is essentially a database for creating, browsing, and searching through information. A wiki allows non-linear, evolving, complex, and networked text, while also allowing for editor argument, debate, and interaction regarding the content and formatting.[10] A defining characteristic of wiki technology is the ease with which pages can be created and updated. Generally, there is no review by a moderator or gatekeeper before modifications are accepted and thus lead to changes on the website. Many wikis are open to alteration by the general public without requiring registration of user accounts. Many edits can be made in real-time and appear almost instantly online, but this feature facilitates abuse of the system. Private wiki servers require user authentication to edit pages, and sometimes even to read them. Maged N. Kamel Boulos, Cito Maramba, and Steve Wheeler write that the open wikis produce a process of Social Darwinism. "... because of the openness and rapidity that wiki pages can be edited, the pages undergo an evolutionary selection process, not unlike that which nature subjects to living organisms. 'Unfit' sentences and sections are ruthlessly culled, edited and replaced if they are not considered 'fit', which hopefully results in the evolution of a higher quality and more relevant page.
        """
        cn_word = """
        人民微博于2010年2月上线，是中央重点新闻网站开办的第一家微博客，具有信息分享、新闻推送、手机和即时通讯工具绑定等功能，累计用户500余万。人民微博突出时政特色，瞄准社会精英群体，打造权威主流声音，致力于构建并拓宽党政机关与人民群众沟通的新渠道。4000余个各级党政机构（包括6个国家部委）、6000余位各级党政干部（其中副部级以上官员达60位）在人民微博与网友在线交流，使人民微博逐步成为各级党政部门和官员问计于民、问需于民、问政于民的首选微博平台。
人民网配备卫星直播车，3G无线直播设备。神九发射，人民网是唯一一家进行视频全程直播的网络媒体。
人民网旗下拥有人民在线、人民视讯、环球网三家控股公司，并在国内各省市设立地方分公司。与此同时，人民网还积极推进全球化布局，先后在日本、美国、美西、韩国，英国、俄罗斯和南非成立分社并设立演播室，大大提升人民网的国际传播力和影响力。
2012年4月27日，人民网在上海证券交易所上市交易（股票代码为“603000”）。它的成功上市创造中国资本市场的两个第一：第一家在国内A股上市的新闻网站，第一家在国内A股整体上市的媒体企业。
        """
        print(Chatbot.summary_v2(cn_word, 2))


    rlist=[
        "AI:string",
        "AI26:人民微博于2010年2月上线，是中央重点新闻网站开办的第一家微博客，具有信息分享、新闻推送、手机和即时通讯工具绑定等功能，累计用户500余万。人民微博突出时政特色，瞄准社会精英群体，打造权威主流声音，致力于构建并拓宽党政机关与人民群众沟通的新渠道。4000余个各级党政机构（包括6个国家部委）、6000余位各级党政干部（其中副部级以上官员达60位）在人民微博与网友在线交流，使人民微博逐步成为各级党政部门和官员问计于民、问需于民、问政于民的首选微博平台。\n人民网配备卫星直播车，3G无线直播设备。神九发射，人民网是唯一一家进行视频全程直播的网络媒体。\n人民网旗下拥有人民在线、人民视讯、环球网三家控股公司，并在国内各省市设立地方分公司。与此同时，人民网还积极推进全球化布局，先后在日本、美国、美西、韩国，英国、俄罗斯和南非成立分社并设立演播室，大大提升人民网的国际传播力和影响力。\n2012年4月27日，人民网在上海证券交易所上市交易（股票代码为“603000”）。它的成功上市创造中国资本市场的两个第一：第一家在国内A股上市的新闻网站，第一家在国内A股整体上市的媒体企业。",
        "AI26:人民微博于2010年2月上线，是中央重点新闻网站开办的第一家微博客，具有信息分享、新闻推送、手机和即时通讯工具绑定等功能，累计用户500余万。人民微博突出时政特色，瞄准社会精英群体，打造权威主流声音，致力于构建并拓宽党政机关与人民群众沟通的新渠道。4000余个各级党政机构（包括6个国家部委）、6000余位各级党政干部（其中副部级以上官员达60位）在人民微博与网友在线交流，使人民微博逐步成为各级党政部门和官员问计于民、问需于民、问政于民的首选微博平台。\n人民网配备卫星直播车，3G无线直播设备。神九发射，人民网是唯一一家进行视频全程直播的网络媒体。\n人民网旗下拥有人民在线、人民视讯、环球网三家控股公司，并在国内各省市设立地方分公司。与此同时，人民网还积极推进全球化布局，先后在日本、美国、美西、韩国，英国、俄罗斯和南非成立分社并设立演播室，大大提升人民网的国际传播力和影响力。\n2012年4月27日，人民网在上海证券交易所上市交易（股票代码为“603000”）。它的成功上市创造中国资本市场的两个第一：第一家在国内A股上市的新闻网站，第一家在国内A股整体上市的媒体企业。",
        "AI26:人民微博于2010年2月上线，是中央重点新闻网站开办的第一家微博客，具有信息分享、新闻推送、手机和即时通讯工具绑定等功能，累计用户500余万。人民微博突出时政特色，瞄准社会精英群体，打造权威主流声音，致力于构建并拓宽党政机关与人民群众沟通的新渠道。4000余个各级党政机构（包括6个国家部委）、6000余位各级党政干部（其中副部级以上官员达60位）在人民微博与网友在线交流，使人民微博逐步成为各级党政部门和官员问计于民、问需于民、问政于民的首选微博平台。\n人民网配备卫星直播车，3G无线直播设备。神九发射，人民网是唯一一家进行视频全程直播的网络媒体。\n人民网旗下拥有人民在线、人民视讯、环球网三家控股公司，并在国内各省市设立地方分公司。与此同时，人民网还积极推进全球化布局，先后在日本、美国、美西、韩国，英国、俄罗斯和南非成立分社并设立演播室，大大提升人民网的国际传播力和影响力。\n2012年4月27日，人民网在上海证券交易所上市交易（股票代码为“603000”）。它的成功上市创造中国资本市场的两个第一：第一家在国内A股上市的新闻网站，第一家在国内A股整体上市的媒体企业。",
        "AI26:人民微博于2010年2月上线，是中央重点新闻网站开办的第一家微博客，具有信息分享、新闻推送、手机和即时通讯工具绑定等功能，累计用户500余万。人民微博突出时政特色，瞄准社会精英群体，打造权威主流声音，致力于构建并拓宽党政机关与人民群众沟通的新渠道。4000余个各级党政机构（包括6个国家部委）、6000余位各级党政干部（其中副部级以上官员达60位）在人民微博与网友在线交流，使人民微博逐步成为各级党政部门和官员问计于民、问需于民、问政于民的首选微博平台。\n人民网配备卫星直播车，3G无线直播设备。神九发射，人民网是唯一一家进行视频全程直播的网络媒体。\n人民网旗下拥有人民在线、人民视讯、环球网三家控股公司，并在国内各省市设立地方分公司。与此同时，人民网还积极推进全球化布局，先后在日本、美国、美西、韩国，英国、俄罗斯和南非成立分社并设立演播室，大大提升人民网的国际传播力和影响力。\n2012年4月27日，人民网在上海证券交易所上市交易（股票代码为“603000”）。它的成功上市创造中国资本市场的两个第一：第一家在国内A股上市的新闻网站，第一家在国内A股整体上市的媒体企业。",
        "AI:",
        "AI:",
        "AI:",
        "AI:A wiki enables communities of editors and contributors to write documents collaboratively. All that people require to contribute is a computer, Internet access, a web browser, and a basic understanding of a simple markup language (e.g. MediaWiki markup language). A single page in a wiki website is referred to as a wiki page, while the entire collection of pages, which are usually well-interconnected by hyperlinks, is the wiki. A wiki is essentially a database for creating, browsing, and searching through information. A wiki allows non-linear, evolving, complex, and networked text, while also allowing for editor argument, debate, and interaction regarding the content and formatting.[10] A defining characteristic of wiki technology is the ease with which pages can be created and updated. Generally, there is no review by a moderator or gatekeeper before modifications are accepted and thus lead to changes on the website. Many wikis are open to alteration by the general public without requiring registration of user accounts. Many edits can be made in real-time and appear almost instantly online, but this feature facilitates abuse of the system. Private wiki servers require user authentication to edit pages, and sometimes even to read them. Maged N. Kamel Boulos, Cito Maramba, and Steve Wheeler write that the open wikis produce a process of Social Darwinism. ... because of the openness and rapidity that wiki pages can be edited, the pages undergo an evolutionary selection process, not unlike that which nature subjects to living organisms. 'Unfit' sentences and sections are ruthlessly culled, edited and replaced if they are not considered 'fit', which hopefully results in the evolution of a higher quality and more relevant page.",
        "AI2256:",
        "AI2:全模式，把句子中所有的可以成词的词语都扫描出来, 速度非常快，但是不能解决歧义；",
        "AI26:人民微博于2010年2月上线，是中央重点新闻网站开办的第一家微博客，具有信息分享、新闻推送、手机和即时通讯工具绑定等功能，累计用户500余万。人民微博突出时政特色，瞄准社会精英群体，打造权威主流声音，致力于构建并拓宽党政机关与人民群众沟通的新渠道。4000余个各级党政机构（包括6个国家部委）、6000余位各级党政干部（其中副部级以上官员达60位）在人民微博与网友在线交流，使人民微博逐步成为各级党政部门和官员问计于民、问需于民、问政于民的首选微博平台。\n人民网配备卫星直播车，3G无线直播设备。神九发射，人民网是唯一一家进行视频全程直播的网络媒体。\n人民网旗下拥有人民在线、人民视讯、环球网三家控股公司，并在国内各省市设立地方分公司。与此同时，人民网还积极推进全球化布局，先后在日本、美国、美西、韩国，英国、俄罗斯和南非成立分社并设立演播室，大大提升人民网的国际传播力和影响力。\n2012年4月27日，人民网在上海证券交易所上市交易（股票代码为“603000”）。它的成功上市创造中国资本市场的两个第一：第一家在国内A股上市的新闻网站，第一家在国内A股整体上市的媒体企业。"
    ]
    prompt_list = CutParent.cutter(rlist)
    for i in prompt_list:
        print("--------")
        print(i)
    # print(test_summary())
    content = "12231:"
    _corn = content.split(":", 1)
    # print(_corn)
    _corn = content.split(":", 1)
    if len(_corn) > 1:
        print("yes")
    # elapsed_time = timeit.timeit(test_summary, number=1)
