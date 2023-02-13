import re


class LangDetector(object):
    """
    检测语言，传入字符串初始化，也可以不传字符串
    """
    # 不能检测出语言的字符
    # 先清理这些字符，再用正则判断unicode判断语言
    remove_characters = u'''[’·°–!"#$%&\'()*+,-./:;<=>?@，。?★、…【】（）《》？“”‘’！[\\]^_`{|}~0-9]+'''
    lang_pattern_list = {
        'zh': re.compile(u"[\u4e00-\u9fff]"),
        'en': re.compile(u'[a-z][A-Z]'),
        'ja': re.compile(u'[\u30a0-\u30ff\u3040-\u309f]'),
        'ko': re.compile(u'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]')
    }
    # 默认使用的语言，识别不了的字符串会默认当作默认语言的字符
    default_lang = 'zh'

    # def __init__(self, text):
    # self.text = text

    def detect(self, text=None, cleaning=True, specific=False, cleaningExclude=False, unknownUseDefault=True):
        # text是不可变对象，因此可以传参
        # if text is None:
        # text = self.text
        if cleaning:
            if cleaningExclude:
                text = self.cleaning_exclude(text)
            else:
                text = self.cleaning_text(text)
        resDict = {}
        # 初始化语言计数用字典
        for lang in self.lang_pattern_list.keys():
            resDict[lang] = 0
        unknown_list = []
        for c in text:
            # 判断语言匹配列表是否匹配成功，如果没有匹配成功，
            # 加入到未知字符列表
            match_flag = False
            for lang, pattern in self.lang_pattern_list.items():
                if pattern.match(c):
                    match_flag = True
                    resDict[lang] += 1
            # 如果匹配不成功，加入未知字符列表
            if not match_flag:
                unknown_list.append(c)

        # 判断是否把未知字符作为默认语言的字符
        if unknownUseDefault:
            for _ in unknown_list:
                resDict[self.default_lang] += 1
            # 清空未知字符列表
            unknown_list.clear()
        result_list = []
        for lang, count in resDict.items():
            if count > 0:
                result_list.append([lang, count / len(text)])
        unknown_num = len(unknown_list)
        if unknown_num > 0:
            result_list.append(['unknown', unknown_num / len(text)])
        # 进行排序
        self.sort_lang_list(result_list)
        # 判断是否返回一个确定的值，默认返回的是各种语言字符串占比的列表
        if specific:
            return result_list[0][0]
        return result_list

    def cleaning_text(self, text):
        return re.sub(self.remove_characters, '', text)

    def cleaning_exclude(self, text):
        patternStr = self.exclude_lang_pattern()
        return re.sub(patternStr, '', text)

    def sort_lang_list(self, lang_list):
        """
        排序的字符串的格式是[['zh', 0.35714285714285715], ['ja', 0.6428571428571429]]
        """

        def sort_key(x):
            return x[1]

        lang_list.sort(key=sort_key, reverse=True)

    def exclude_lang_pattern(self):
        concatStr = ''
        for pattern in self.lang_pattern_list.values():
            concatStr += pattern.pattern
        tempstr = concatStr.replace('[', '').replace(']', '')
        return f'[^{tempstr}]'
