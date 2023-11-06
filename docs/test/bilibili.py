# -*- coding: utf-8 -*-
# @Time    : 2023/8/22 下午2:15
# @Author  : sudoskys
# @File    : _bilibili.py
# @Software: PyCharm
import json

import inscriptis
from bilibili_api import search, sync, video_zone


async def test_f_search_by_order():
    return await search.search_by_type("ウサギの現実は逃げる", search_type=search.SearchObjectType.VIDEO,
                                       order_type=search.OrderVideo.TOTALRANK, time_range=10, page=1)


res = sync(test_f_search_by_order())
print(json.dumps(res, indent=4, ensure_ascii=False))


async def search_on_bilibili(keywords):
    _result = await search.search_by_type(
        keyword=keywords,
        search_type=search.SearchObjectType.VIDEO,
        order_type=search.OrderVideo.TOTALRANK,
        page=1
    )
    _video_list = _result.get("result")
    if not _video_list:
        return "Search Not Success"
    _video_list = _video_list[:3]  # 只取前三
    _info = []
    for video in _video_list:
        _video_title = inscriptis.get_text(video.get("title"))
        _video_author = video.get("author")
        _video_url = video.get("arcurl")
        _video_tag = video.get("tag")
        _video_play = video.get("play")
        _video_info = f"标题：{_video_title}\n作者：{_video_author}\n链接：{_video_url}\n标签：{_video_tag}\n播放量：{_video_play}"
        _info.append(_video_info)
    return "\n\n".join(_info)
