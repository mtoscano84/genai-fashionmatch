# Deploy the Fashionmatch App on CloudRun

## Before you begin
1. Open a new terminal and set the following environment variables
```
export BACKEND_SERVICE_NAME='fashionmatch-backend'
export REGION='us-central1'
export PROJECT_ID='fashion-item-recommendation'

2. Enable APIs:
```
gcloud services enable artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com \
                       run.googleapis.com
```
3. Go to the recommendation service directory
```
cd fashionmatch-service
```

```
4. Set the variable host on the [CONNECTION] section of the config.ini file to the AlloyDB Private IP
Get the AlloyDB Private IP
```

```

Update the config.ini file
```
;This module defines data access variables
[CORE]
PROJECT = fashion-item-recommendation
LOCATION = us-central1
LANDING_REPO = landing-image-repo01
CATALOG_REPO = catalog-repo
DB_PASS = Welcome1
DB_HOST = 127.0.0.1
DB_NAME = fashionstore
#SECONDS_PER_JOB = 2

[CONNECTION]
host = 10.143.0.7
port = 5432
database = fashionstore
user = postgres
password = Welcome1
```


1. Make sure you have a Google Cloud project and billing is enabled.

2. Set your PROJECT_ID environment variable:
```
export PROJECT_ID=<YOUR_PROJECT_ID>
```

## Cloud Run

3. [Install](https://cloud.google.com/sdk/docs/install) the gcloud CLI.

4. Set gcloud project:
```
gcloud config set project $PROJECT_ID
```
5. Enable APIs:
```
gcloud services enable alloydb.googleapis.com \
                       compute.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       servicenetworking.googleapis.com \
                       vpcaccess.googleapis.com \
                       aiplatform.googleapis.com
