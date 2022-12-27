# -*- coding: utf-8 -*-
# @Time    : 12/27/22 8:00 PM
# @FileName: plugins.py
# @Software: PyCharm
# @Github    ：sudoskys
import openai_async
from openai_async.utils.Talk import Talk


class PromptTool(object):
    @staticmethod
    def isStrIn(prompt: str, keywords: list):
        isIn = False
        for i in keywords:
            if i in prompt:
                isIn = True
        return isIn

    @staticmethod
    def isStrAllIn(prompt: str, keywords: list):
        isIn = True
        for i in keywords:
            if i not in prompt:
                isIn = False
        return isIn

    @staticmethod
    def match_enhance(prompt):
        import re
        match = re.findall(r"\[(.*?)\]", prompt)
        match2 = re.findall(r"\"(.*?)\"", prompt)
        match3 = re.findall(r"\((.*?)\)", prompt)
        match.extend(match2)
        match.extend(match3)
        return match


class NlP(object):
    @staticmethod
    def get_webServerStopSentence():
        return openai_async.webServerStopSentence

    @staticmethod
    def get_is_filter_url():
        return openai_async.webServerUrlFilter

    @staticmethod
    def nlp_filter_list(prompt, material: list):
        if not material or not isinstance(material, list):
            return []
        # list 互相匹配
        while len(material) >= 2:
            prev_len = len(material)
            _pre = material[0]
            _afe = material[1]
            sim = Talk.simhash_similarity(pre=_pre, aft=_afe)
            if sim < 15:
                _remo = _afe if len(_afe) > len(_pre) else _pre
                # 移除过于相似的
                material.remove(_remo)
            if len(material) == prev_len:
                break
        while len(material) >= 2:
            prev_len = len(material)
            material_len = len(material)
            for i in range(0, len(material), 2):
                if i + 1 >= material_len:
                    continue
                _pre = material[i]
                _afe = material[i + 1]
                sim = Talk.cosion_sismilarity(pre=_pre, aft=_afe)
                if sim > 0.6:
                    _remo = _afe if len(_afe) > len(_pre) else _pre
                    # 移除过于相似的
                    material.remove(_remo)
                    material_len = material_len - 1
            if len(material) == prev_len:
                break
        # 关键词算法匹配
        _key = Talk.tfidf_keywords(prompt, topK=7)
        _returner = []
        for i in material:
            for ir in _key:
                if ir in i:
                    _returner.append(i)
        return _returner
