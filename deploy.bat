@echo off
echo Starting deployment process...

REM Enable required APIs
echo Enabling required Google Cloud APIs...
call gcloud services enable compute.googleapis.com
call gcloud services enable vpcaccess.googleapis.com
call gcloud services enable appengine.googleapis.com

REM Check and create VPC connector only if it doesn't exist
echo Checking VPC connector...
call gcloud compute networks vpc-access connectors list --region=us-central1 | findstr "app-connector" > nul
if errorlevel 1 (
    echo Creating VPC connector...
    call gcloud compute networks vpc-access connectors create app-connector ^
        --network=default ^
        --region=us-central1 ^
        --range=10.8.0.0/28
) else (
    echo VPC connector already exists
)

REM Check and create static IP only if it doesn't exist
echo Checking static IP...
call gcloud compute addresses list --global | findstr "dr-wasim-ip" > nul
if errorlevel 1 (
    echo Reserving static IP...
    call gcloud compute addresses create dr-wasim-ip --global --ip-version=IPV4
) else (
    echo Static IP already exists
)

REM Get the IP address
echo Getting reserved IP...
for /f %%i in ('gcloud compute addresses describe dr-wasim-ip --global --format="get(address)"') do set IP_ADDRESS=%%i

echo Reserved IP address: %IP_ADDRESS%
echo Please verify this IP is in MongoDB Atlas Network Access whitelist

REM Clean up old versions (keep at least 2 versions)
echo Cleaning up old versions...
for /f "skip=2" %%v in ('gcloud app versions list --sort-by=~version.createTime --format="value(version.id)"') do (
    echo Deleting old version: %%v
    call gcloud app versions delete %%v --quiet
)

REM Deploy with specific settings
echo Deploying application...
call gcloud app deploy app.yaml --quiet --promote --stop-previous-version

echo Deployment completed!
pause
