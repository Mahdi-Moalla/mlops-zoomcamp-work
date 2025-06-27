Q3: 2
Q4: 
aws --endpoint-url=http://localhost:4566 s3 mb s3://nyc-duration

#####################################################
export S3_ENDPOINT_URL=http://localhost:4566
export INPUT_FILE_PATTERN="s3://nyc-duration/in/{year:04d}-{month:02d}.parquet"
export OUTPUT_FILE_PATTERN="s3://nyc-duration/out/{year:04d}-{month:02d}.parquet"

#########################################################
 aws --endpoint-url=http://localhost:4566 s3 cp ./data/yellow_tripdata_2023-03.parquet s3://nyc-duration/in/2023-03.parquet

#########################################################
 (mlops_6) mahdi@DESKTOP-2MHI7LI:~/work/mlops_6$ aws --endpoint-url=http://localhost:4566 s3 ls
2025-06-25 19:25:21 nyc-duration
(mlops_6) mahdi@DESKTOP-2MHI7LI:~/work/mlops_6$ aws --endpoint-url=http://localhost:4566 s3 ls s3://nyc-duration
                           PRE in/
(mlops_6) mahdi@DESKTOP-2MHI7LI:~/work/mlops_6$ aws --endpoint-url=http://localhost:4566 s3 ls s3://nyc-duration/in
                           PRE in/
(mlops_6) mahdi@DESKTOP-2MHI7LI:~/work/mlops_6$ aws --endpoint-url=http://localhost:4566 s3 ls s3://nyc-duration/in/
2025-06-25 19:47:06   56127762 2023-03.parquet
#########################################################

Q5:
2025-06-25 19:59:13       3620 2023-01.parquet
2025-06-25 19:47:06   56127762 2023-03.parquet

########################################################
 aws --endpoint-url=http://localhost:4566 s3 cp s3:/
/nyc-duration/out/2023-01.parquet .

Q6:
 np.float64(36.27725045203073)
