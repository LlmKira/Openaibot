import json
from typing import List

import requests
from duckduckgo_search import AsyncDDGS
from loguru import logger
from pydantic import BaseModel


class SearchEngine(BaseModel):
    api_key: str

    def search(self, search_term: str):
        raise NotImplementedError


class SearchEngineResult(BaseModel):
    title: str
    link: str
    snippet: str


class SerperSearchEngine(SearchEngine):
    api_key: str

    async def search(self, search_term: str) -> List[SearchEngineResult]:
        url = "https://google.serper.dev/search"
        payload = json.dumps(
            {
                "q": search_term,
            }
        )
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        result_list = response.json()["organic"]
        _result = []
        logger.debug(f"Got {len(result_list)} results")
        for item in result_list:
            _result.append(
                SearchEngineResult(
                    title=item.get("title", "Undefined"),
                    link=item.get("link", "Undefined"),
                    snippet=item.get("snippet", "Undefined"),
                )
            )
        _result = _result[:4]
        return _result


async def search_in_duckduckgo(search_sentence: str):
    try:
        search_result = await AsyncDDGS().text(
            search_sentence, safesearch="off", timelimit="y", max_results=10
        )
    except Exception as e:
        raise ValueError(
            f"Search Failed: DuckDuckGo Error now not available: {type(e)}"
        )
    else:
        _build_result = []
        for result in search_result:
            _build_result.append(
                SearchEngineResult(
                    title=result.get("title", "Undefined"),
                    link=result.get("href", "Undefined"),
                    snippet=result.get("body", "Undefined"),
                )
            )
        return _build_result


def build_search_tips(search_items: List[SearchEngineResult], limit=5):
    search_tips = []
    assert isinstance(
        search_items, list
    ), f"Search Result should be a list, but got {type(search_items)}"
    for index, item in enumerate(search_items):
        if index >= limit:
            break
        search_tips.append(
            f"<doc id={index} link={item.link} title={item.title}> "
            f"\n{item.snippet}\n"
            f"<doc>"
        )
    return "Search Api:\n" + "\n".join(search_tips)
