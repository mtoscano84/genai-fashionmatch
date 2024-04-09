GCLOUD_BIN=`which gcloud`

LOG_DATE=`date`
echo "###########################################################################################"
echo "${LOG_DATE} Deploying image to Cloud Run....."
"${GCLOUD_BIN}" run deploy ${FRONTEND_SERVICE_NAME} --source . --platform managed --region ${REGION} --allow-unauthenticated

LOG_DATE=`date`
echo "###########################################################################################"
echo "${LOG_DATE} Execution finished! ..."
