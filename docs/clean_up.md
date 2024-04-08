# Clean up

The fastest way to clean up is to delete the entire Google Cloud project. Follow
the steps below if you want to keep the project but delete resources created
through this demo.

## Before you begin

1. Set your PROJECT_ID environment variable:

    ```bash
    export PROJECT_ID=<YOUR_PROJECT_ID>
    ```

## Deleting Cloud Run deployment resources

1. Delete the Frontend Cloud Run service deployed:

    ```bash
    gcloud run services delete fashionmatch-app
    ```

2. Delete the Backend Cloud Run service deployed:

    ```bash
    gcloud run services delete fashionmatch-backend
    ```

## Delete Database resources

[Clean up Alloydb](./alloydb.md#clean-up-resources)
