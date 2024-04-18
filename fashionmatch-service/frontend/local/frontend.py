#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Image Similarity Search - FrontEnd
"""

#Code management
from configparser import ConfigParser
import logging
import datetime
import base64
import io
#Flask imports
from flask_cors import CORS
from flask import Flask, request
#Other imports
import json
import re
import requests
# Gradio and Interface imports
import gradio as gr
from PIL import Image
import requests
#Google Cloud imports
from google.cloud import storage

#Load variables
variables = ConfigParser()
variables.read("config.ini")

# Read variables
project = variables.get("CORE","PROJECT")
location = variables.get("CORE","LOCATION")
landing_repo = variables.get("CORE","LANDING_REPO")
catalog_repo = variables.get("CORE","CATALOG_REPO")
result_img_list = [] 

API_URL="http://localhost:8080"
#API_URL="https://image-search-app-kjhc5kxmrq-uc.a.run.app"
GEN_DATA_EMB="/find_similar_images"
GET_QUERY="/get_query"

# Get an input file from Gradio Interfece and upload it to GCS
def process_image(file_path, max_price, in_stock_only):
  """
  Processes an image by extracting its name, uploading it to Google Cloud Storage, retrieving similar images based on embedding analysis, and converting them to PIL format for display

  :param str file_patg: Path to the local image file to be processed.
  :return list result_img_pil_list: A list of PIL image objects representing similar images retrieved based on the uploaded image
  """
  result_img_pil = []
  image_name = _extract_last_field(file_path)
  image_uri = _upload_file_to_gcs(file_path, image_name, landing_repo)

  stock = str(in_stock_only) 
  url = API_URL + GEN_DATA_EMB
  response = requests.get(url, params={"project": project, "location": location, "image_name": image_name, "landing_repo": landing_repo, "in_stock_only": stock, "max_price": max_price})

  result_img_list = response.json()
  # Prepare output for Gradio in PIL format
  for result_img_name in result_img_list:
    result_img_pil_list = _convert_jpg_to_pil (catalog_repo, result_img_name, result_img_pil)

  return result_img_pil_list

def show_query(max_price, in_stock_only):
  """
  Returns the QUERY TEXT executed to the Database

  :params int max_price: Maximum price selected on the filter
  :params boolean in_stock_only: Shows the value of the filter stock
  :return jpeg image_arch: Image return
  """
  stock = str(in_stock_only)
  mode = 1 # No filters
  if stock == "True":
     if max_price != 0:
        mode = 2 # All filters enabled
     else:
        mode = 3 # Stock ON, Max_Price Off
  else:
      if max_price != 0:
        mode = 4 # Stock Off, Max_price On  
  url = API_URL + GET_QUERY
  response = requests.get(url, params={"mode": mode})  

  result_query_list = response.json()
  result_query = result_query_list['query_text']

  image_bytes = _read_gcs_file_to_bytes("fashion_item_recommendation_app.png", catalog_repo)
  image_as_pil = Image.open(io.BytesIO(image_bytes))
  image_arch = gr.Image(image_as_pil) 

  return result_query, image_arch

def _read_gcs_file_to_bytes(image_name, repo):
  """
  Reads a file from a GCS bucket as bytes, given an image_name and a bucket name

  :param str image_name: Name of the file to read
  :param str bucket_name: Name of the source GCS bucket
  :return str image_bytes: Retreived file in bytes
  """
  storage_client = storage.Client()
  bucket = storage_client.bucket(repo)
  blob = bucket.blob(image_name)

  image_bytes = blob.open("rb").read()
  return image_bytes

def _convert_jpg_to_pil (catalog_repo, result_img_name, result_img_pil):
  """
  Reads a JPEG image from GCS and converts to PIL format

  :param str catalog_repo: Name of the file to read
  :param str result_image_name: Name of the source GCS bucket
  :return list result_img_pil: Retreived file in bytes
  """

  # Read an image from GCS and convert to PIL format
  storage_client = storage.Client()
  bucket = storage_client.bucket(catalog_repo)
  blob = bucket.get_blob(result_img_name)
  # Open the file in binary mode to avoid encoding errors
  # Copy the file to keep it accesible outside the WITH block

  image_bytes = blob.open("rb").read()
  result_img_pil.append(Image.open(io.BytesIO(image_bytes)))
 
  return result_img_pil

def _upload_file_to_gcs(file_path, image_name, bucket_name):
  """
  Uploads a file to GCS under a specific name and bucket, returning its URI

  :param str file_path: Path to the file to be uploaded
  :param str image_name: Name to be assigned to the uploaded file in GCS
  :return str bucket_name: Name of the GCS bucket where the file will be uploaded
  :return str blob_uri: String representing the URI of the uploaded file in GCS
  """

  # Create a StorageServiceClient object
  storage_client = storage.Client()

  # Get or create the destination bucket
  destination_bucket = storage_client.bucket(bucket_name)
  blob = destination_bucket.blob(image_name)

  # Check if the blob exists before uploading
  blob_exists = blob.exists()

  if not blob_exists:
    # Upload the file and get its URI
    blob.upload_from_filename(file_path)
    file_uri = f"gs://{bucket_name}/{image_name}"
    logging.info(f"File uploaded successfully: {file_uri}")
    return file_uri
  else:
    logging.warning(f"File already exists: {image_name}")
    return None

def _extract_last_field(string):
  """
  Extracts the last field from a string, assuming it is separated by slash ("/") characteres

  :param str string: String containing multiple fields separated by slash characteres
  :return str last_field: String containing the last field extracted from the original string after the final slash
  """
  return re.split('/', string)[-1]

with gr.Blocks() as gradio_app:
    gr.Markdown(
    """
    # Welcome to GenFashionStore
    Start uploading an image to get recommendations !

    ## Your Picture
    """)
    with gr.Row(): 
        with gr.Column(scale=1):  # Fixed-width filter column
            image = gr.Image(label="Upload your picture", type='filepath')
            gr.Markdown(
            """ 
            ## Filters 
            Adjust your search using filters
            """)
            with gr.Row():  # Row for filters
                filters = gr.Group()
                with filters:
                    price_range = gr.Slider(0, 300, label="Price Range", value=0)
                    in_stock_only = gr.Checkbox(label="In Stock Only", value=False)
                    near_me = gr.Checkbox(label="Near me", value=False)
                    discount = gr.Checkbox(label="Discount", value=False)                  
            button1 = gr.Button("Search")
        with gr.Column(scale=3):  # Flexible results column
            gr.Markdown(""" ## You might be interested in """)
            with gr.Row():
              output_images = gr.Gallery(label="Similar items", preview=True, format="jpeg")
            gr.Markdown(""" ## Under the hood """)
            button2 = gr.Button("Show me") 
            image_output = gr.Image(label="Architecture", visible=True)
            output_text = gr.Textbox(label="Query")

    button1.click(process_image, inputs=[image, price_range, in_stock_only], outputs=[output_images])
    button2.click(show_query, inputs=[price_range,in_stock_only], outputs=[output_text, image_output])
    
#gradio_app.launch(host="localhost",port=8080,debug=False)
gradio_app.launch(server_name="0.0.0.0",server_port=8090,debug=False)