#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Image Similarity Search - Backend
"""

#Code management
from configparser import ConfigParser
import logging
#Other imports
import base64
import re
import typing
#Flask imports
from flask_cors import CORS
from flask import Flask, request
# DataManagement
import sqlalchemy
import asyncio
import asyncpg
from datastore import Datastore
#Google Cloud imports
from google.cloud import storage
from google.cloud import aiplatform
from google.protobuf import struct_pb2

#Init logging
logging.basicConfig(level=logging.INFO)

#Init flask
app = Flask(__name__)
CORS(app)
#

#Variable
table_name = "image_lookup"
config_file_path = "config.ini"

#Services
@app.get("/find_similar_images")
def find_similar_images():
  """
  http://localhost:8080/get_similar_images?project_id=bigquery-public-data&location=us-central1&encodedString=b"adasdsad"&image_name=asdasd
  
  Analyzes an input image, generates its embedding, stores it in a database, and returns the top 5 closest image paths based on similar visual features
  """
  project = request.args.get("project",type=str)
  location = request.args.get("location",type=str)
  image_name = request.args.get("image_name",type=str)
  landing_repo = request.args.get("landing_repo",type=str)
  stock = request.args.get("stock",type=str)
  max_price = request.args.get("max_price",type=int)

  # Read the image from the bucket in binary format
  image_bytes = _read_gcs_file_to_bytes (image_name, landing_repo)
  # Encode the image in string format
  encodedString = _encode_image_to_base64 (image_bytes)

  api_regional_endpoint = f"{location}-aiplatform.googleapis.com"
  client_options = {"api_endpoint": api_regional_endpoint}
  client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

  endpoint = f"projects/{project}/locations/{location}/publishers/google/models/multimodalembedding@001"
  instance = struct_pb2.Struct()
  image_struct = instance.fields["image"].struct_value
  image_struct.fields["bytesBase64Encoded"].string_value = encodedString
  instances = [instance]
  response = client.predict(endpoint=endpoint, instances=instances)
  
  # Generate the embedding
  image_embedding: typing.Sequence[float]
  image_emb_value = response.predictions[0]['imageEmbedding']
  image_embedding = [v for v in image_emb_value]

  # Load the image_name and the embedding in the Database
  ds = Datastore(None, config_file_path)
  image_id=asyncio.run(_load_embedding(image_name,image_embedding, ds))
  if image_id is None:
    logging.info("There was an error while loading the embedding to the database")
    return 0
  else:
    logging.info("The embedding image has been loadaed in the database")
    # Calculate the top 5 nearest vectors in the Database
    image_path_results=asyncio.run(_find_image_match(image_id, stock, max_price, ds))
    return image_path_results

@app.get("/get_query")
def get_query():
  mode = request.args.get("mode",type=int)

  ds = Datastore(None, config_file_path)
  query_text=asyncio.run(_show_query(mode, ds))
  
  return {"query_text": query_text}

# Auxiliary Functions
def _read_gcs_file_to_bytes(image_name, landing_repo):
  """
  Reads a file from a GCS bucket as bytes, given an image_name and a bucket name

  :param str image_name: Name of the file to read
  :param str bucket_name: Name of the source GCS bucket
  :return str image_bytes: Retreived file in bytes
  """
  storage_client = storage.Client()
  bucket = storage_client.bucket(landing_repo)
  blob = bucket.blob(image_name)

  image_bytes = blob.open("rb").read()
  return image_bytes

# Convert ImageByte to Base64 String
def _encode_image_to_base64(image_bytes):
  """
  Converts raw image byte data into a Base64-encoded string

  :param byte image_byte: Byte string containing raw image data
  :return str encodedString: Encoded representation of the raw image data
  """
  encodedString = base64.b64encode(image_bytes).decode("utf-8") 
  return encodedString

async def _load_embedding(image_name, image_embedding, ds):
  """
  Inserts an image embedding into a PostgreSQL database table and returns the IDs of matching entries based on the image name

  :param str image_name: Name of the image to insert in the database
  :param list image_embedding: Embedding representation of an image
  :return int image_id: ID from the embedding image inserted in the database
  """
  await ds.create_conn()
  await ds.insert_emb_to_db(image_name, image_embedding)
  result=await ds.get_imageid_from_lookup(image_name)
  await ds.close()

  return result

async def _find_image_match(image_id, stock, max_price, ds):
  """
  Search for 5 matches on the catalog for the input image_id

  :param int image_id:ID from the embedding image inserted in the database
  :return list image_path_results: List of the 5 images matches
  """
  await ds.create_conn()
  if stock == "True":
    image_path_list=await ds.image_search_in_stock_only(image_id, max_price)
  else:
    image_path_list=await ds.image_search(image_id, max_price)
  
  image_path_results = [ e[0] for e in image_path_list ]
  await ds.close()

  return image_path_results

async def _show_query(mode, ds):
  """
  Returns the QUERY TEXT executed to the Database

  :params int max_price: Maximum price selected on the filter
  :params boolean in_stock_only: Shows the value of the filter stock
  :return jpeg image_arch: Image return
  """
  await ds.create_conn()
  sql_query_text=await ds.get_sql_text(mode)
  await ds.close() 

  return sql_query_text

if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)