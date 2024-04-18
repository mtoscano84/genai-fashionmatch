# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import asyncpg

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Literal, Optional

import asyncpg
from pydantic import BaseModel

import os
import configparser
import csv

class Datastore():
    __pool: asyncpg.Pool
    config = None

    def kind(cls):
        return "postgres"

    def __init__(self, pool: asyncpg.Pool, config_file_path):
        self.__pool = pool
        self.__config = configparser.ConfigParser()
        self.__config.read(config_file_path)
       
    async def create_conn(self):
        """
        Create the DB configuration reading the parameters from the config.ini file
        """
        self.__pool = await asyncpg.create_pool(
            host=str(self.__config.get("CONNECTION", "host")),
            user=self.__config.get("CONNECTION", "user"),
            password=self.__config.get("CONNECTION", "password"),
            database=self.__config.get("CONNECTION", "database"),
            port=self.__config.get("CONNECTION", "port"),
        )
        if self.__pool is None:
            raise TypeError("pool not instantiated")
        return self.__pool
    
    async def initialize_db(self):
        """
        Configure the vector extension and create the tables needed
        """
        async with self.__pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS catalog CASCADE")
           # If the table already exists, drop it to avoid conflicts
            await conn.execute("DROP TABLE IF EXISTS image_lookup CASCADE")
            # Create a new table
            await conn.execute(
                """
                CREATE TABLE catalog(
                ID INT PRIMARY KEY, 
                PATH varchar,
                PRICE INT,
                UNITS INT, 
                EMBEDDING VECTOR(1408)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE image_lookup(
                ID bigserial, 
                PATH varchar not null, 
                EMBEDDING VECTOR(1408),
                PRIMARY KEY (ID, PATH)
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE queries(
                MODE int, 
                QUERY_TEXT text
                )
                """
            )

    async def insert_from_csv(self, csv_file_path, table_name, columns):
        """
        Inserts data from a CSV file into a PostgreSQL table.

        :param str csv_file_path: The path to the CSV file
        :param str table_name: The name of the table to insert into
        :param list columns: A list of column names in the CSV file (matching the table)
        """

        try:
            column_str = ', '.join(columns)
            placeholders = ', '.join(['$' + str(i) for i in range(1, len(columns) + 1)])

            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)  # Use DictReader for matching headers
                for row in reader:
                    values = [int(row[col]) for col in columns]
                    query = f"INSERT INTO {table_name} ({column_str}) VALUES ({placeholders})"
                    async with self.__pool.acquire() as conn:
                        await conn.execute(query, *values)

        except (FileNotFoundError, asyncpg.PostgresError) as e:
            print(f"Error during CSV insertion: {e}")     
    
    async def load_queries_table(self):
        """
        Executes a series of SQL INSERT to the quieres table

        """
        queries = [
            (1, 'SELECT path FROM catalog ORDER BY embedding <-> (SELECT embedding FROM image_lookup WHERE ID = $1) LIMIT 3'),
            (2, 'SELECT path FROM catalog WHERE units != 0 and price < $2 ORDER BY embedding <-> (SELECT embedding FROM image_lookup WHERE ID = $1) LIMIT 3'),
            (3, 'SELECT path FROM catalog WHERE units != 0 ORDER BY embedding <-> (SELECT embedding FROM image_lookup WHERE ID = $1) LIMIT 3'),
            (4, 'SELECT path FROM catalog WHERE price < $2 ORDER BY embedding <-> (SELECT embedding FROM image_lookup WHERE ID = $1) LIMIT 3')
        ]

        async with self.__pool.acquire() as conn:
            async with conn.cursor() as cur:
                for mode, query_text in queries:
                    try:
                        await cur.execute("INSERT INTO queries (MODE, QUERY_TEXT) VALUES (%s, %s)", (mode, query_text))
                    except Exception as e:
                        print(f"Error inserting query for mode {mode}: {e}")  # Basic error handling

                await conn.commit()    

    async def load_emb_to_db(self, table_name, image_name, image_embedding, image_id):
        """
        Update the catalog table to include the embedding of an image

        :param str table_name: The path to the CSV file
        :param str image_name: The name of the table to insert into
        :param list image_embedding: Embedding representation of an image
        :param int image_id: ID from the embedding image
        """
        str_image_embedding = str(image_embedding).replace("['","")
        query = f"UPDATE {table_name} SET PATH = $1, EMBEDDING = $2 WHERE ID = $3" 
        async with self.__pool.acquire() as conn:
            await conn.execute(query, image_name, str_image_embedding, image_id)

    async def insert_emb_to_db(self, image_name, image_embedding):
        """
        Inserts the embedding of an input image into the image_lookup table.

        :param str image_name: The name of the table to insert into
        :param list image_embedding: Embedding representation of an image
        """
        str_image_embedding = str(image_embedding).replace("['","")
        query = f"INSERT INTO image_lookup (PATH, EMBEDDING) VALUES ($1, $2)"
        async with self.__pool.acquire() as conn:
            await conn.execute(query, image_name, str_image_embedding)
    
    async def get_imageid_from_catalog(self, image_name):
        """
        Get the image id for a image_name from the catalog table 

        :param str image_name: The name of the table to insert into
        :param int image_id: ID from the image_name
        """
        result = await self.__pool.fetchrow(
            """
              SELECT ID from catalog where PATH = $1
            """,
            image_name
        )

        if result is None:
            return None
        return result

    async def get_imageid_from_lookup(self, image_name):
        """
        Get the image id for a image_name from the image_lookup table 

        :param str image_name: The name of the table to insert into
        :param int image_id: ID from the image_name
        """
        result = await self.__pool.fetchval(
            """
              SELECT ID from image_lookup where PATH = $1
            """,
            image_name
        )

        if result is None:
            return None
        return result
    
    async def image_search(self, image_id, max_price):
        """
        Get the top5 nearest image IDs from the catalog using a image_id from the image_lookup table

        :param int image_id: ID from the image_name
        :param list results: Lists of the top5 nearest image IDs
        """
        if max_price == 0:
            results = await self.__pool.fetch(
            """
            SELECT path
            FROM
                catalog 
            ORDER BY
                embedding
            <-> 
                (
                SELECT embedding
                FROM
                image_lookup
                WHERE
                ID = $1)
            LIMIT 3
            """,
            image_id
            )
        else:
            results = await self.__pool.fetch(
            """
            SELECT path
            FROM
                catalog
            WHERE
                 price < $2
            ORDER BY
                embedding
            <-> 
                (
                SELECT embedding
                FROM
                image_lookup
                WHERE
                ID = $1)
            LIMIT 3
            """,
            image_id, max_price
            )

        if results is None:
            return None
        return results 

    async def image_search_in_stock_only(self, image_id, max_price):
        """
        Get the top5 nearest image IDs from the catalog using a image_id from the image_lookup table

        :param int image_id: ID from the image_name
        :param list results: Lists of the top5 nearest image IDs
        """
        if max_price == 0:
            results = await self.__pool.fetch(
            """
            SELECT path
            FROM
                catalog
            WHERE
                units != 0 
            ORDER BY
                embedding
            <-> 
                (
                SELECT embedding
                FROM
                image_lookup
                WHERE
                ID = $1)
            LIMIT 3
            """,
            image_id
            )
        else:
            results = await self.__pool.fetch(
            """
            SELECT path
            FROM
                catalog
            WHERE
                units != 0 and
                price < $2
            ORDER BY
                embedding
            <-> 
                (
                SELECT embedding
                FROM
                image_lookup
                WHERE
                ID = $1)
            LIMIT 3
            """,
            image_id, max_price
            )

        if results is None:
            return None
        return results

    async def get_sql_text(self, mode):
        """
        Get the top5 nearest image IDs from the catalog using a image_id from the image_lookup table

        :param int image_id: ID from the image_name
        :param list results: Lists of the top5 nearest image IDs
        """
        results = await self.__pool.fetchrow(
            """
            SELECT 
                QUERY_TEXT
            FROM
                queries
            WHERE
                MODE = $1
            """,
            mode
            )

        if results is None:
            return None
        query_text = results[0]
        return query_text                                          

    async def close(self):
        await self.__pool.close()