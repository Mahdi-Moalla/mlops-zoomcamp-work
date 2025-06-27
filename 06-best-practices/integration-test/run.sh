#!/usr/bin/env bash

cd "$(dirname "$0")"

export S3_ENDPOINT_URL=http://localhost:4566
export INPUT_FILE_PATTERN="s3://nyc-duration/in/{year:04d}-{month:02d}.parquet"
export OUTPUT_FILE_PATTERN="s3://nyc-duration/out/{year:04d}-{month:02d}.parquet"


docker compose up -d

sleep 2

echo '####################################'
echo 'testing write_data'

aws --endpoint-url=$S3_ENDPOINT_URL s3 mb s3://nyc-duration

sleep 1

python  -c 'import integration_testing; integration_testing.test_save_data()'

rm *.parquet

aws --endpoint-url=$S3_ENDPOINT_URL s3 cp s3://nyc-duration/in/2023-01.parquet .

if [ ! -f  ./2023-01.parquet ];  then
    docker compose logs
    docker compose down
    exit 1
fi

rm *.parquet

echo '####################################'
echo 'testing read_data'

#export S3_ENDPOINT_URL=http://localhost:5566

python  -c 'import integration_testing; integration_testing.test_read_data()'

ERROR_CODE=$?

if [ ${ERROR_CODE} != 0 ]; then
    docker compose logs
    docker compose down
    exit ${ERROR_CODE}
fi

docker compose down
