# GenAI Fashion Item Recommendation

Note: This project is for demonstration only and is not an officially supported Google product.

## Introduction

This project demonstrates how we can provide our application with advanced search capabilities based on techniques such as embeddings and vector searches to improve the user experience.

The demo shows the search module of an online fashion store. The search engine is able to recommend items from our catalog based on an image provided.

Specifically, the demo showcases the following:

- **Image embedding**: The system extracts a vector representation (embedding) from the uploaded image.
- **Vector search**: The system compares the extracted embedding to a database of embeddings of known items in the catalog.
- **Recommendation**: The system recommends items that are similar to the uploaded image based on the results of the vector search.

## Table of Contents
<!-- TOC depthfrom:2 -->

- [Introduction](#introduction)
- [Table of Contents](#table-of-contents)
- [Understanding the demo](#understanding-the-demo)
    - [Understanding Image Embedding](#understanding-image-embedding)
    - [Using Vector Search](#using-vector-search)
    - [Architecture](#architecture)
- [Deploying](#deploying)
    - [Before you begin](#before-you-begin)
    - [Setting up your Database](#setting-up-your-database)
    - [Deploying the Recommendation Service](#deploying-the-recomendation-service)
    - [Running the Recommendation Service](#running-the-recommendation-service)
    - [Clean up Resources](#clean-up-resources)

<!-- /TOC -->

## Understanding the demo
### Understanding Image Embedding
Image embedding simplifies image analysis by converting images into numerical vectors (embeddings) that capture their visual essence. Vertex AI's Multimodal API leverages a powerful pre-trained model to generate these embeddings, enabling tasks like image classification, visual search, and content moderation.

Key Benefits
- **Powerful Pre-Trained Model**: Vertex AI's model is trained on vast datasets, giving it a deep understanding of visual concepts. This eliminates the need to train your own models from scratch.
- **Semantic Understanding**: The model generates embeddings that capture the meaning within images, allowing for similarity comparisons that go beyond pixel-by-pixel analysis.
- **Versatility**: The Vertex AI Multimodal API can handle images, video, and text, opening up possibilities for cross-media analysis and search.

### Using Vector Search
Vector search allows you to find items in a database that are semantically similar to a query, even if they don't share exact keywords. The pgvector extension for PostgreSQL provides tools for storing vectors, creating indexes, and performing vector search operations. AlloyDB, Google's fully-managed PostgreSQL-compatible database, offers specific optimizations for vector search, making it an excellent platform for these applications.

Key Benefits of Using AlloyDB with pgvector
- **Performance**: AlloyDB has built-in optimizations for vector search operations, allowing you to perform similarity-based searches on large datasets with incredible speed.
- **Scalability**: AlloyDB's ability to scale seamlessly ensures that your vector search applications can handle growing data and complex queries without performance bottlenecks.
- **Operational Simplicity**: As a fully-managed service, AlloyDB handles administration tasks, backups, and updates, letting you focus on application development and leveraging optimized vector search features.

### Architecture
![Architecture](images/fashion_item_recommendation_app.png)

This architecture provides an image-based product recommendation system. It leverages Vertex AI to analyze images and generate meaningful representations of their visual content. These representations are stored in AlloyDB for fast similarity searches, allowing the system to recommend visually similar products to users based on their image submissions.

There 3 key components in this architecture: 
- **Cloud Run**: Hosts the frontend and backend components of the recommendation service, providing a serverless platform for code execution.
- **Vertex AI Multimodal Embedding**: Generates the image embedding from a pretrained model. Vertex AI provides a managed platform for creating, deploying, and using these multimodal embedding models.
- **AlloyDB for PostgreSQL**: Stores the image embeddings and relevant catalog item data, providing high-performance, scalable storage, and data retrieval for recommendations.

## Deploying

Deploying this demo consists of 3 steps:

1. Creating your database and initializing it with data
2. Deploying the Recommendation Service -- deploying your recommendation service and connecting it to your database
3. Running the Recommendation Service

### Before you begin
Clone this repo to your local machine:
```
git clone https://github.com/mtoscano84/genai-fashionmatch.git
```

### Setting up your Database
The recommendation service uses a database to store the image embeddings and perform similarity searches to generate recommendations based on the catalog.

Follow these instructions to set up and configure the database

[Setting up your Database](docs/alloydb.md)

### Deploying the Recommendation Service
The Recommendation service is based on two Cloud Run services:

1. **Frontend**: Manages the user interface and orchestrates the calls needed to process requests and display the recommended items.
2. **Backend**: Orchestrates the generation of the embedding from the image provided by the user, its insertion into the database, and the similarity search to obtain the catalog items.

To deploy the recommendation service, follow these instructions:

[Deploy the Recommendation Service](docs/deploy_recommendation_service.md)

### Running the Recommendation Service
Start uploading a picture to get recommendations !

![GenAI FashionStore](https://screencast.googleplex.com/api/gif/NTMzNDQ1OTY5NDk3MjkyOHw2YTBiZTFjOS0zMg/image)

### Clean up Resources
[Instructions for cleaning up resources](./docs/clean_up.md)




