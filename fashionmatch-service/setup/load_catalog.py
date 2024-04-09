#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Image Similarity App - Batch Load
"""

#Code management
from configparser import ConfigParser
import logging
#Other imports
import base64
import re
import typing
import time
import configparser
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

#Load variables
config_file_path = "config.ini"
csv_file_path = "../../data/fashion_catalog_dataset.csv"
variables = ConfigParser()
variables.read(config_file_path)

# Read variables
project = variables.get("CORE","PROJECT")
location = variables.get("CORE","LOCATION")
catalog_repo = variables.get("CORE","CATALOG_REPO")
location = variables.get("CORE","LOCATION")
table_name = "catalog"
image_id = 1
seconds_per_job=2
blob_uri_list = []

def generate_and_store_image_embedding(project, location, file_uri, image_id, ds):
  """
  Retrieves the image embedding vector for a specified image file in GCS, using Vertex AI multi-model API and storing the result in a database

  :param str project: String representing the Google Cloud project for AI Platform access
  :param list location: String specifying the AI Platform location for the prediction model
  :param list file_uri: String containing the Google Cloud Storage URI of the image file
  :return json image_name: JSON object containing the image name that was stored in the database
  """
  # Read the image from the bucket in binary format
  image_bytes, image_name = _get_gcs_file_bytes (file_uri)
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
  
  image_embedding: typing.Sequence[float]
  image_emb_value = response.predictions[0]['imageEmbedding']
  image_embedding = [v for v in image_emb_value]
  time.sleep(seconds_per_job)
  result=asyncio.run(_load_embedding(table_name,image_name,image_embedding, image_id, ds))

  if result is None:
    logging.info("There was an error while loading the embedding to the database")
    return 0
  else:
    logging.info(f"The embedding image has been loadaed in the database: {image_name}")
    return {"ImageName": image_name}

async def _load_embedding(table_name, image_name, image_embedding,image_id, ds):
  """
  Inserts an image embedding into a PostgreSQL database table and returns the IDs of image inserted

  :param str image_name: Name of the image to insert in the database
  :param list image_embedding: Embedding representation of an image
  :param list image_id: ID of the image_name to insert the embedding
  :return list result: ID of the embeding image inserted
  """
  await ds.create_conn()
  await ds.load_emb_to_db(table_name, image_name, image_embedding, image_id)
  result=await ds.get_imageid_from_catalog(image_name)
  await ds.close()

  return result

def _get_gcs_file_bytes(file_uri):
  """
  Retrieves the raw bytes and filename of an image stored in GCS based on its URI

  :param str file_uri: String containing the GCS URI of the image
  :return byte image_byte: Byte string containing the raw data of the downloaded image file
  :return str image_name: Filename of the downloaded image extracted from the URI
  """
  storage_client = storage.Client()
  bucket_name = file_uri.split("/")[2]
  image_name = file_uri.split("/")[3] 
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(image_name)

  image_bytes = blob.open("rb").read()
  return image_bytes, image_name

def _list_gcs_bucket_objects(bucket_name):
  """
  Retrieves a list of GCS URIs for all files (excluding directories) within a specified bucket

  :param str bucket_name: Name of the GCS Bucket
  :return list blob_uri_list: List of strings containing the GCS URIs for each file within the specified bucket
  """
  client = storage.Client()
  bucket = client.get_bucket(bucket_name)

  # List all the blobs in the specified folder
  blobs = bucket.list_blobs(delimiter=None)

  # Iterate through each blob and read its content
  for blob in blobs:
    if not blob.name.endswith("/"):  # Ignore directories
      image_name = blob.name
      blob_uri = "gs://" + bucket_name + "/" + image_name
      blob_uri_list.append(blob_uri)
  return blob_uri_list

def _encode_image_to_base64(image_bytes):
  """
  Converts raw image byte data into a Base64-encoded string

  :param byte image_byte: Byte string containing raw image data
  :return str encodedString: Encoded representation of the raw image data
  """
  encodedString = base64.b64encode(image_bytes).decode("utf-8") 
  return encodedString

async def init_database(ds) -> None:
  """
  Create the table and insert the data from a csv file into the database
  """
  columns = ['ID', 'PRICE', 'UNITS'] 
  await ds.create_conn()
  await ds.initialize_db()
  await ds.insert_from_csv(csv_file_path, table_name, columns)
  await ds.close()

  logging.info("Database init done")

if __name__ == '__main__':
  ds = Datastore(None, config_file_path)
  asyncio.run(init_database(ds))
  image_uri_list = _list_gcs_bucket_objects(catalog_repo)
  image_uri_list_filtered = image_uri_list[:100]
  for image in image_uri_list_filtered:
    generate_and_store_image_embedding(project, location, image, image_id, ds)
    image_id = image_id + 1
