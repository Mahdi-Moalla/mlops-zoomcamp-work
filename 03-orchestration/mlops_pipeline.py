import textwrap
from datetime import datetime, timedelta

from airflow.sdk import dag, task


from mlops_code import (pipeline_init,
                        init_tmp_folder,
                        generate_data_dates,
                        download_raw_data,
                        prepare_data,
                        preprocess_data,
                        ml_train)

#@dag(user_defined_macros={'venv_python':'/home/venvs/mlops_venv/bin/python'})

@dag()
def mlops_pipeline(year=2023,
                   month=5,
                   train_sampling=0.1,
                   val_sampling=0.1,
                   test_sampling=0.1,
                   pipeline_tmp_folder='/home/airflow_tmp/mlops_tmp',
                   keep_folder=True,
                   mlflow_tracking_url='http://mlflow-server:5000',
                   mlflow_experiment_name='nyc-yellow-taxi-regressor',
                   venv_python= '/home/venvs/mlops_venv/bin/python'):
    
    ctx=pipeline_init(year,
                      month,
                      train_sampling,
                      val_sampling,
                      test_sampling,
                      pipeline_tmp_folder,
                      keep_folder,
                      mlflow_tracking_url,
                      mlflow_experiment_name)
    
    ctx=init_tmp_folder(ctx) 
    ctx=generate_data_dates(ctx)

    for split_name in ['train','val','test']:
        ctx=download_raw_data(ctx,split_name)

    ctx=prepare_data(ctx)
    ctx=preprocess_data(ctx)
    ctx=ml_train(ctx)


mlops_pipeline()
