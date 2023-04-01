# -*- coding: utf-8 -*-
# @Time    : 2023/3/31 下午9:06
# @Author  : sudoskys
# @File    : test_data.py
# @Software: PyCharm
import os

import loguru
import pytest
from dotenv import load_dotenv

from Component.data import MongoClientWrapper
from utils.data import DictUpdate


class TestDataUtils(object):

    def test_merge(self):
        import json
        _result = DictUpdate.deep_merge_dicts({"a": {"rss": "5"}, "c": 6}, {"b": 2, "a": {"rss": "6"}})
        # Sort
        _results = json.dumps(_result, sort_keys=True)

        assert _results == '{"a": {"rss": "6"}, "b": 2, "c": 6}'


load_dotenv()
URI = os.getenv('MONGODB_DSN', "mongodb://localhost:27017/")


class TestMongoClientWrapper:
    @pytest.mark.asyncio
    async def test_ping(self):
        mongo_wrapper = MongoClientWrapper(URI)
        assert await mongo_wrapper.ping() == True

        # invalid URI
        _test = False
        try:
            invalid_uri = "mongodb://localhost:0000/"
            invalid_mongo_wrapper = MongoClientWrapper(invalid_uri)
        except Exception as e:
            _test = isinstance(e, Exception)
        assert _test == True

    @pytest.mark.asyncio
    async def test_insertion_and_finding(self):
        mongo_wrapper = MongoClientWrapper(URI, db_name="test_db", collection_name="test_collection")
        doc1 = {"name": "John", "age": 30}

        # Inserting documents
        result = await mongo_wrapper.insert_one(doc1)
        assert result.acknowledged == True
        _id = result.inserted_id
        assert _id is not None

        result = await mongo_wrapper.insert_many(
            [{'i': i} for i in range(20)])
        assert len(result.inserted_ids) == 20

        # Finding documents
        query = {"name": "John"}
        result = await mongo_wrapper.find_one(query)
        assert result["name"] == "John"

        query = {"age": {"$gt": 20}}
        results = await mongo_wrapper.find_many(query)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_update_and_deletion(self):
        mongo_wrapper = MongoClientWrapper(URI, db_name="test_db", collection_name="test_collection")
        doc = {"name": "Alex", "age": 35}

        # Inserting document
        result = await mongo_wrapper.insert_one(doc)
        assert result.acknowledged == True

        # Updating document
        filter_query = {"name": "Alex"}
        update_query = {"$set": {"age": 40}}
        result = await mongo_wrapper.update_one(filter_query, update_query)
        assert result.modified_count == 1

        # Deleting document
        query = {"name": "Alex"}
        result = await mongo_wrapper.delete_one(query)
        assert result.deleted_count == 1
