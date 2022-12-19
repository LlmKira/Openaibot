# -*- coding: utf-8 -*-
# @Time    : 12/9/22 9:35 PM
# @FileName: nltk_test.py
# @Software: PyCharm
# @Github    ：sudoskys
# from openai_async.Chat import Talk, Chatbot
# import nltk

from openai_async.Chat.text_analysis_tools.api.keyphrase.keyphrase import KeyPhraseExtraction
from openai_async.Chat.text_analysis_tools.api.keywords.tfidf import TfidfKeywords
from openai_async.Chat.text_analysis_tools.api.summarization.tfidf_summarization import TfidfSummarization
from openai_async.Chat.text_analysis_tools.api.text_similarity.cosion import CosionSimilarity
from openai_async.Chat.text_analysis_tools.api.text_similarity.edit import EditSimilarity
from openai_async.Chat.text_analysis_tools.api.text_similarity.simhash import SimHashSimilarity
from openai_async.Chat.text_analysis_tools.api.summarization.textrank_summarization import TextRankSummarization

# nltk.download('punkt')
en_word = """
        A wiki enables communities of editors and contributors to write documents collaboratively. All that people require to contribute is a computer, Internet access, a web browser, and a basic understanding of a simple markup language (e.g. MediaWiki markup language). A single page in a wiki website is referred to as a "wiki page", while the entire collection of pages, which are usually well-interconnected by hyperlinks, is "the wiki". A wiki is essentially a database for creating, browsing, and searching through information. A wiki allows non-linear, evolving, complex, and networked text, while also allowing for editor argument, debate, and interaction regarding the content and formatting.[10] A defining characteristic of wiki technology is the ease with which pages can be created and updated. Generally, there is no review by a moderator or gatekeeper before modifications are accepted and thus lead to changes on the website. Many wikis are open to alteration by the general public without requiring registration of user accounts. Many edits can be made in real-time and appear almost instantly online, but this feature facilitates abuse of the system. Private wiki servers require user authentication to edit pages, and sometimes even to read them. Maged N. Kamel Boulos, Cito Maramba, and Steve Wheeler write that the open wikis produce a process of Social Darwinism. "... because of the openness and rapidity that wiki pages can be edited, the pages undergo an evolutionary selection process, not unlike that which nature subjects to living organisms. 'Unfit' sentences and sections are ruthlessly culled, edited and replaced if they are not considered 'fit', which hopefully results in the evolution of a higher quality and more relevant page.
        """
cn_word = """
        人民微博于2010年2月上线，是中央重点新闻网站开办的第一家微博客，具有信息分享、新闻推送、手机和即时通讯工具绑定等功能，累计用户500余万。人民微博突出时政特色，瞄准社会精英群体，打造权威主流声音，致力于构建并拓宽党政机关与人民群众沟通的新渠道。4000余个各级党政机构（包括6个国家部委）、6000余位各级党政干部（其中副部级以上官员达60位）在人民微博与网友在线交流，使人民微博逐步成为各级党政部门和官员问计于民、问需于民、问政于民的首选微博平台。
人民网配备卫星直播车，3G无线直播设备。神九发射，人民网是唯一一家进行视频全程直播的网络媒体。
人民网旗下拥有人民在线、人民视讯、环球网三家控股公司，并在国内各省市设立地方分公司。与此同时，人民网还积极推进全球化布局，先后在日本、美国、美西、韩国，英国、俄罗斯和南非成立分社并设立演播室，大大提升人民网的国际传播力和影响力。
2012年4月27日，人民网在上海证券交易所上市交易（股票代码为“603000”）。它的成功上市创造中国资本市场的两个第一：第一家在国内A股上市的新闻网站，第一家在国内A股整体上市的媒体企业。
        """


# res = #Talk().cut_ai_prompt(prompt=cn_word)
# for i in res:
#    print("----")
#    print(i)


def keyphrase_extract(topk=100, method='tfidf', with_word=True, save_pic=False, with_mask=True):
    """
    关键短语抽取
    :param topk: 提取多少关键词组成短语
    :param method: 提取关键词的方法
    :param with_word: 关键词是否作为短语进行输出
    :param save_pic: 是否生成词云图片，保存路径
    :param with_mask: 生成图片是否使用背景
    :return:
    """
    test = """
    该研究主持者之一、波士顿大学地球与环境科学系博士陈池（音）表示，“尽管中国和印度国土面积仅占全球陆地的9%，但两国为这一绿化过程贡献超过三分之一。考虑到人口过多的国家一般存在对土地过度利用的问题，这个发现令人吃惊。”
NASA埃姆斯研究中心的科学家拉玛·内曼尼（Rama Nemani）说，“这一长期数据能让我们深入分析地表绿化背后的影响因素。我们一开始以为，植被增加是由于更多二氧化碳排放，导致气候更加温暖、潮湿，适宜生长。”
“MODIS的数据让我们能在非常小的尺度上理解这一现象，我们发现人类活动也作出了贡献。”
NASA文章介绍，在中国为全球绿化进程做出的贡献中，有42%来源于植树造林工程，对于减少土壤侵蚀、空气污染与气候变化发挥了作用。
据观察者网过往报道，2017年我国全国共完成造林736.2万公顷、森林抚育830.2万公顷。其中，天然林资源保护工程完成造林26万公顷，退耕还林工程完成造林91.2万公顷。京津风沙源治理工程完成造林18.5万公顷。三北及长江流域等重点防护林体系工程完成造林99.1万公顷。完成国家储备林建设任务68万公顷。
    """
    key_phrase_extractor = KeyPhraseExtraction(topk=topk, method=method, with_word=with_word)
    key_phrase = key_phrase_extractor.key_phrase_extraction(test)
    print("keyphrase result: {}\n".format(key_phrase))


# keyphrase_extract()


"""
文本摘要
tfidf_summarization
"""


def tfidf_summarization(ratio=0.5):
    """
    采用tfidf进行摘要抽取
    :param ratio: 摘要占文本长度的比例
    :return:
    """
    doc = """
        该研究主持者之一、波士顿大学地球与环境科学系博士陈池（音）表示，“尽管中国和印度国土面积仅占全球陆地的9%，但两国为这一绿化过程贡献超过三分之一。考虑到人口过多的国家一般存在对土地过度利用的问题，这个发现令人吃惊。”
    NASA埃姆斯研究中心的科学家拉玛·内曼尼（Rama Nemani）说，“这一长期数据能让我们深入分析地表绿化背后的影响因素。我们一开始以为，植被增加是由于更多二氧化碳排放，导致气候更加温暖、潮湿，适宜生长。”
    “MODIS的数据让我们能在非常小的尺度上理解这一现象，我们发现人类活动也作出了贡献。”
    NASA文章介绍，在中国为全球绿化进程做出的贡献中，有42%来源于植树造林工程，对于减少土壤侵蚀、空气污染与气候变化发挥了作用。
    据观察者网过往报道，2017年我国全国共完成造林736.2万公顷、森林抚育830.2万公顷。其中，天然林资源保护工程完成造林26万公顷，退耕还林工程完成造林91.2万公顷。京津风沙源治理工程完成造林18.5万公顷。三北及长江流域等重点防护林体系工程完成造林99.1万公顷。完成国家储备林建设任务68万公顷。
        """
    summ = TfidfSummarization(ratio=ratio)
    summ = summ.analysis(cn_word)
    print("tfidf summarization result: {}\n".format(summ))


def tfidf_keywords(delete_stopwords=False, topK=1, withWeight=False):
    """
    tfidf 提取关键词
    :param delete_stopwords: 是否删除停用词
    :param topK: 输出关键词个数
    :param withWeight: 是否输出权重
    :return: [(word, weight), (word1, weight1)]
    """
    tfidf = TfidfKeywords(delete_stopwords=delete_stopwords, topK=topK, withWeight=withWeight)
    keywords = tfidf.keywords("假如正在")
    print("tfidf keywords result: {}\n".format(keywords))


def edit_similarity():
    """
    采用编辑距离计算文本之间的相似性
    :return: 编辑距离
    """
    edit = EditSimilarity()
    edit_dis = edit.edit_dist("爱看的电影是行星", "你还记得爱看的电影吗")
    print("edit distance: {}\n".format(edit_dis))


def simhash_similarity():
    """
    采用simhash计算文本之间的相似性
    :return:
    """
    simhash = SimHashSimilarity()
    sim = simhash.run_simhash(
        "ここすき,这里意为喜欢,通常被用在弹幕之中,是对视频某一片段表达赞赏用的. 似乎只有在中国才会被缩写为kksk（ここkokoすきsuki）.",
        "2022年2月16日 · 最近,网红在痞幼发了一个开团了,导致蔡徐坤的黑粉们疯狂晒cxk的黑图,从而导致大量cxk的粉丝来骂痞幼,事后痞幼迅速出来道歉说自己说的开团了是游戏")
    print("simhash result: {}\n".format(sim))


def cosion_sismilarity():
    """
    基于余弦计算文本相似性
    :return: 余弦值
    """
    text1 = "ここすき,这里意为喜欢,通常被用在弹幕之中,是对视频某一片段表达赞赏用的. 似乎只有在中国才会被缩写为kksk（ここkokoすきsuki）."
    text2 = "2021年11月25日 · kksk在网络中并不是“看看谁快”的中文拼音首字母的缩写,而是来自日本的一个二次元用语,即日语“ここ好き”的罗马音“ko ko SU KI”的缩写,意思是“喜欢"
    cosion = CosionSimilarity()
    similiar = cosion.similarity(text1, text2)
    print("cosion similarity result: {}\n".format(similiar))


doc = """
    LDA（Latent Dirichlet Allocation）是一种主题建模方法，它根据文档库中主题的出现概率分配词语，使用LDA模型可以把文档集分成不同的主题。MMR（Maximal Marginal Relevance）是一种检索算法，可以根据文档中关键词的相似性来提取最相关的句子。TextRank是基于图的排序算法，可以根据文本内容之间的关系来提取文章的关键片段。Text_teaser是一种基于聚类的摘要算法，可以根据文本的内容进行聚类，并生成摘要。
    """


def textrank_summarization(sentence, ratio=0.2):
    """
    采用tfidf进行摘要抽取
    :param ratio: 摘要占文本长度的比例
    :return:
    """
    summ = TextRankSummarization(ratio=ratio)
    summ = summ.analysis(sentence)
    print("textrank summarization result: {}\n".format(summ))


history_list = [
    "1122",
    "Ai:我的软肋是看不透舍不得输不起放不下每个人都有自己的人生冷暖自知。无论生活还是网络好象都是一场旅行。前路漫漫。不可能把所有的美丽与美景尽收眼底总有一些人和事会被自己遗忘在路上虽然有时我们并不想扔下这些曾经的美好 学会接受残缺是人生的成熟人无完人缺憾是人生的常态人生有成就有败有聚就有散没有谁能得天独厚一手。遮天鱼和熊掌不可兼得不强求凡事尽人事随缘而安追求。完美是美好的理想接受残缺是美好的心态我的软肋是看不透舍不得输不起放不下每个人都有自己的人生冷暖自知。无论生活还是网络好象都是一场旅行。前路漫漫。不可能把所有的美丽与美景尽收眼底总有一些人和事会被自己遗忘在路上虽然有时我们并不想扔下这些曾经的美好 学会接受残缺是人生的成熟人无完人缺憾是人生的常态人生有成就有败有聚就有散没有谁能得天独厚一手。遮天鱼和熊掌不可兼得不强求凡事尽人事随缘而安追求。我的软肋是看不透舍不得输不起放不下每个人都有自己的人生冷暖自知。无论生活还是网络好象都是一场旅行。前路漫漫。不可能把所有的美丽与美景尽收眼底总有一些人和事会被自己遗忘在路上虽然有时我们并不想扔下这些曾经的美好 学会接受残缺是人生的成熟人无完人缺憾是人生的常态人生有成就有败有聚就有散没有谁能得天独厚一手。遮天鱼和熊掌不可兼得不强求凡事尽人事随缘而安追求。",
    "Human:Using OpenAi's Aeve chatGPT func|在 Telegram ",
    "Human:Using OpenAi's Apihieve chatGPT func|在 Telegram ",
    "Human:Using OpenAi's Api hatGPT func|在 Telegram ",
    "Human:Using OpenAi's egram to achieve chatGPT func|在 Telegram ",
    "Human:Using OpenAi'sto achieve chatGPT func|在 Telegram ",
    "AI:Using OpenAi's Api on Telee chatGPT func|在 Telegram ",
    "Human:Using OpenAi'so achieve chatGPT func|在 Telegram ",
    "AI:在python中判断 list 中是否包含某个元素"
]

# tfidf_keywords()
# CutParent = Chatbot(api_key="none", conversation_id="none")
# prompt = CutParent.Summer(
#     prompt="习近平强调，中方坚定支持突方走符合自身国情的发展道路，反对外部势力干涉突尼斯内政，相信突方有智慧、有能力维护国家稳定和发展。",
#     extra_token=500,
#     memory=history_list)
# for i in prompt:
#    print(i)
# cosion_sismilarity()
doc = """
       该研究主持者之一、波士顿大学地球与环境科学系博士陈池（音）表示，“尽管中国和印度国土面积仅占全球陆地的9%，但两国为这一绿化过程贡献超过三分之一。考虑到人口过多的国家一般存在对土地过度利用的问题，这个发现令人吃惊。”
   NASA埃姆斯研究中心的科学家拉玛·内曼尼（Rama Nemani）说，“这一长期数据能让我们深入分析地表绿化背后的影响因素。我们一开始以为，植被增加是由于更多二氧化碳排放，导致气候更加温暖、潮湿，适宜生长。”
   “MODIS的数据让我们能在非常小的尺度上理解这一现象，我们发现人类活动也作出了贡献。”
   NASA文章介绍，在中国为全球绿化进程做出的贡献中，有42%来源于植树造林工程，对于减少土壤侵蚀、空气污染与气候变化发挥了作用。
   据观察者网过往报道，2017年我国全国共完成造林736.2万公顷、森林抚育830.2万公顷。其中，天然林资源保护工程完成造林26万公顷，退耕还林工程完成造林91.2万公顷。京津风沙源治理工程完成造林18.5万公顷。三北及长江流域等重点防护林体系工程完成造林99.1万公顷。完成国家储备林建设任务68万公顷。
"""
print(1)
print(tfidf_summarization(ratio=0.4))
