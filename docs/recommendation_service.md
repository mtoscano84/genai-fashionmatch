# Deploy the Fashionmatch App on CloudRun

## Before you begin
1. Go to the recommendation service directory
```
cd fashionmatch-service
```
2. Open a new terminal and set the following environment variables
```
export BACKEND_SERVICE_NAME='fashionmatch-backend'
export REGION='us-central1'
export PROJECT_ID='fashion-item-recommendation'
```
4. Deploy the backend cloud run service
```


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
