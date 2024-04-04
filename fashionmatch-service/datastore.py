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

    async def insert_from_csv(self, csv_file_path, table_name, columns):
        """Inserts data from a CSV file into a PostgreSQL table.

        Args:
            csv_file_path (str): The path to the CSV file.
            table_name (str): The name of the table to insert into.
            columns (list): A list of column names in the CSV file (matching the table).
        """

        try:
            column_str = ', '.join(columns)
            placeholders = ', '.join(['$' + str(i) for i in range(1, len(columns) + 1)])

            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)  # Use DictReader for matching headers
                for row in reader:
                    print(f"Row values: {row}")
                    values = [int(row[col]) for col in columns]
                    print(f"Values: {values}")
                    query = f"INSERT INTO {table_name} ({column_str}) VALUES ({placeholders})"
                    print(f"query: {query}")
                    async with self.__pool.acquire() as conn:
                        await conn.execute(query, *values)

        except (FileNotFoundError, asyncpg.PostgresError) as e:
            print(f"Error during CSV insertion: {e}")     

    async def load_emb_to_db(self, table_name, image_name, image_embedding, image_id):
        """Inserts data into the specified table.

        Args:
            table_name (str): The name of the table to insert into.
            data (dict): A dictionary containing the columns and their values.
        """
        str_image_embedding = str(image_embedding).replace("['","")
#        query = f"INSERT INTO {table_name} (PATH, EMBEDDING) VALUES ('" + image_name + "',array" + str_image_embedding + ");"
#        query = f"UPDATE {table_name} SET PATH = '" + image_name + "', EMBEDDING = array" + str_image_embedding + "WHERE ID = {image_id}"
        query = f"UPDATE {table_name} SET PATH = $1, EMBEDDING = $2 WHERE ID = $3"
        print(f"Query Update: {query}")
#        await self.conn.execute(query, *values)  
        async with self.__pool.acquire() as conn:
            await conn.execute(query, image_name, str_image_embedding, image_id)
    
    async def get_imageid_by_image_name(self, image_name: str):
        result = await self.__pool.fetch(
            """
              SELECT ID from catalog where PATH = $1
            """,
            image_name,
        )

        if result is None:
            return None
        return result        

    async def close(self):
        await self.__pool.close()