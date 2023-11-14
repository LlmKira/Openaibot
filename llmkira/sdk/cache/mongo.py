# -*- coding: utf-8 -*-
# @Time    : 2023/3/31 下午9:46
# @Author  : sudoskys
# @File    : mongo.py
# @Software: PyCharm
import asyncio

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient


class MongoClientWrapper:
    def __init__(self, url, db_name=None, collection_name=None):
        self.client = AsyncIOMotorClient(url)
        if db_name and collection_name:
            self._set_db_and_collection(db_name, collection_name)

    async def ping(self):
        try:
            await self.client.server_info()  # test connection
            await self.client.list_database_names()  # test authentication
        except Exception as e:
            logger.debug(f'⚠️ Mongodb {e}')
            return False
        return True

    def _copy_with_changes(self, **kwargs):
        new_instance = type(self).__new__(type(self))
        new_instance.__dict__.update(self.__dict__)
        new_instance.__dict__.update(kwargs)
        return new_instance

    def with_database(self, db_name):
        return self._copy_with_changes(db=self.client[db_name])

    def with_collection(self, collection_name):
        return self._copy_with_changes(collection=self.db[collection_name])

    def _set_db_and_collection(self, db_name, collection_name):
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    async def insert_one(self, document):
        result = await self.collection.insert_one(document)
        return result

    async def insert_many(self, documents):
        result = await self.collection.insert_many(documents)
        return result

    async def find_one(self, query):
        result = await self.collection.find_one(query)
        return result

    async def find_many(self, query):
        result = await self.collection.find(query).to_list(length=None)
        return result

    async def update_one(self, filter_query, update_query):
        result = await self.collection.update_one(filter_query, update_query)
        return result

    async def delete_one(self, query):
        result = await self.collection.delete_one(query)
        return result


# Test
if __name__ == '__main__':
    async def main():
        # create a new instance of the MongoClientWrapper class
        mongo = MongoClientWrapper('mongodb://localhost:27017').with_database('test').with_collection('test')
        await mongo.ping()

        # set the database and collection to use

        # insert a document
        result = await mongo.insert_one({'name': 'John', 'age': 30})
        print(result.inserted_id)

        # find a document by query
        result = await mongo.find_one({'name': 'John'})
        print(result)

        # update a document
        filter_query = {'name': 'John'}
        update_query = {'$set': {'age': 31}}
        result = await mongo.update_one(filter_query, update_query)
        print(result.modified_count)

        # delete a document
        query = {'name': 'John'}
        result = await mongo.delete_one(query)
        print(result.deleted_count)

        result = await mongo.insert_many(
            [{'i': i} for i in range(2000)])
        print('inserted %d docs' % (len(result.inserted_ids),))


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
