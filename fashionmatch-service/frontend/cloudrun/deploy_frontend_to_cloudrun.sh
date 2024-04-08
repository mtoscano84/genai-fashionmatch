GCLOUD_BIN=`which gcloud`

LOG_DATE=`date`
echo "###########################################################################################"
echo "${LOG_DATE} Deploying image to Cloud Run....."
"${GCLOUD_BIN}" run deploy ${FRONTED_SERVICE_NAME} --source . --platform managed --region ${REGION} --allow-unauthenticated

LOG_DATE=`date`
echo "###########################################################################################"
echo "${LOG_DATE} Execution finished! ..."
