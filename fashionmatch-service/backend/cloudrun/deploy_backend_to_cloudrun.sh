GCLOUD_BIN=`which gcloud`

LOG_DATE=`date`
echo "###########################################################################################"
echo "${LOG_DATE} Deploying image to Cloud Run....."
"${GCLOUD_BIN}" beta run deploy ${BACKEND_SERVICE_NAME} --source . --platform managed --network my-vpc --subnet my-subnet --vpc-egress private-ranges-only --region ${REGION} --allow-unauthenticated

LOG_DATE=`date`
echo "###########################################################################################"
echo "${LOG_DATE} Execution finished! ..."
