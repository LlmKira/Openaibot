# -*- coding: utf-8 -*-
# @Time    : 11/9/22 8:46 AM
# @FileName: DfaDetect.py
# @Software: PyCharm
# @Github    ：spirit-yzk


class QueryDetector:
    @staticmethod
    def has_keyword(sentence, keywords) -> bool:
        return any(keyword in sentence for keyword in keywords)

    @staticmethod
    def is_need_help(sentence) -> bool:
        help_keywords = [
            '怎么做', 'How', 'how', 'what', 'What', 'Why', 'why', '复述', '复读', '要求你', '原样', '例子',
            '解释', 'exp', '推荐', '说出', '写出', '如何实现', '代码', '写', 'give', 'Give',
            '请把', '请给', '请写', 'help', 'Help', '写一', 'code', '如何做', '帮我', '帮助我', '请给我', '什么',
            '为何', '给建议', '给我', '给我一些', '请教', '建议', '怎样', '如何', '怎么样',
            '为什么', '帮朋友', '怎么', '需要什么', '注意什么', '怎么办', '助け', '何を', 'なぜ', '教えて', '提案', '何が',
            '何に',
            '何をす', '怎麼做', '複述', '復讀', '原樣', '解釋', '推薦', '說出', '寫出', '如何實現', '代碼', '寫',
            '請把', '請給', '請寫', '寫一', '幫我', '幫助我', '請給我', '什麼', '為何', '給建議', '給我',
            '給我一些', '請教', '建議', '步驟', '怎樣', '怎麼樣', '為什麼', '幫朋友', '怎麼', '需要什麼',
            '註意什麼', '怎麼辦'
        ]
        return QueryDetector.has_keyword(sentence, help_keywords)

    @staticmethod
    def is_query(sentence) -> bool:
        query_keywords = [
            "怎么", "How",
            "什么", "作用", "知道", "吗？", "什么", "认识", "What", "bilibili", "http",
            "what", "who", "how", "Who",
            "Why", "的作品", "why", "Where",
            "了解", "简述一下", "How to", "how to",
            "解释", "怎样的", "新闻", "ニュース", "电影", "番剧", "アニメ",
            "2022", "2023", "请教", "介绍", "怎样", "吗", "么", "？", "?", "呢"
        ]
        return QueryDetector.has_keyword(sentence, query_keywords)

    @staticmethod
    def is_code(sentence) -> bool:
        code_keywords = [
            '("', '")', ").", "()", "!=", "==", "print_r(", "var_dump(", 'NSLog( @', 'println(', '.log(',
            'print(', 'printf(', 'WriteLine(', '.Println(', '.Write(', 'alert(', 'echo('
        ]
        return QueryDetector.has_keyword(sentence, code_keywords)


class Cn(object):
    @staticmethod
    def is_chinese(word):
        for ch in word:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

    @staticmethod
    def is_contain_chinese(check_str):
        for ch in check_str:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False
