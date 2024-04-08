# fashion-item-recommendation

Note: This project is for demonstration only and is not an officially supported Google product.

# Introduction

This demo showcases a Fashion Item Recommendation based on image simalarity search. The application provides an user interface to upload an image and get recomended items from your catalog. The code provided here is designed to show how you can combine GenAI, VertexAI and AlloyDB to provide advanced search capabilities to your application.

# Architecture

The diagram show the architecture of the demo

![Architecture](images/fashion_item_recommendation_app.png)

# Deploying

Deploying this demo consists of 3 steps:

1. creating your database and initializing it with data
2. Deploying your service -- deploying your recommendation service and connecting it to your database
3. Running the Recommendation

## Before you begin
Clone this repo to your local machine:
```
git clone https://github.com/mtoscano84/genai-fashionmatch.git
```

## Setting up your Database
The recommendation service uses a database to store the image embeddings and perform similarity searches to generate recommendations based on the catalog.

Follow these instructions to set up and configure the database

[Setting up your Database](docs/alloydb.md)

## Deploying the Recommendation Service
The Recommendation service is based on two Cloud Run services:

1. **Frontend**: Manages the user interface and orchestrates the calls needed to process requests and display the recommended items.
2. **Backend**: Orchestrates the generation of the embedding from the image provided by the user, its insertion into the database, and the similarity search to obtain the catalog items.

To deploy the recommendation service, follow these instructions:

[Deploy the Recommendation Service](docs/deploy_recommendation_service.md)

## Running the Recommendation Service
Instructions for running app locally

## Clean up Resources
Instructions for cleaning up resources

# Writing your own Recommendation Service




