import textwrap
from datetime import datetime, timedelta

from airflow.sdk import dag, task


@task.external_python(python="{{ params.venv_python }}")
def pipeline_init(year,
                  month,
                  train_sampling,
                  val_sampling,
                  test_sampling,
                  pipeline_tmp_folder,
                  keep_folder,
                  mlflow_tracking_url,
                  mlflow_experiment_name):

    from addict import Dict
    import mlflow
    
    ctx=Dict()

    ctx.data.train.sampling=train_sampling
    ctx.data.val.sampling=val_sampling
    ctx.data.test.sampling=test_sampling

    ctx.run.year=year
    ctx.run.month=month

    ctx.run.pipeline_tmp_folder=pipeline_tmp_folder
    ctx.run.keep_folder=keep_folder
    ctx.run.mlflow_tracking_url=mlflow_tracking_url
    ctx.run.mlflow_experiment_name=mlflow_experiment_name

    
    mlflow.set_tracking_uri(ctx.run.mlflow_tracking_url)
    mlflow.set_experiment(ctx.run.mlflow_experiment_name)
    
    with mlflow.start_run() as run:
        ctx.run.mlflow.run_id=run.info.run_id

    return ctx.to_dict()

@task.external_python(python="{{ params.venv_python }}")
def init_tmp_folder(ctx):

    from addict import Dict
    import os
    import os.path as osp

    ctx=Dict(ctx)
    print(ctx.run.pipeline_tmp_folder)
    if osp.isdir(ctx.run.pipeline_tmp_folder):
        assert ctx.run.keep_folder or \
                not os.listdir(ctx.run.pipeline_tmp_folder),\
                'Given raw data is not empty!'
    else:
        os.makedirs(ctx.run.pipeline_tmp_folder)

    return ctx.to_dict()



@task.external_python(python="{{ params.venv_python }}")
def generate_data_dates(ctx):

    from addict import Dict
    from datetime import date
    from dateutil.relativedelta import relativedelta

    ctx=Dict(ctx)

    year=ctx.run.year
    month=ctx.run.month
    
    assert month<=12

    input_date=date(year=year, month=month, day=1)
    assert input_date < date.today(), 'invalid year/month'

    prev_month = input_date + relativedelta(months=-1)
    prev2_month = input_date + relativedelta(months=-2)

    ctx.data.test.date=input_date
    ctx.data.val.date=prev_month
    ctx.data.train.date=prev2_month

    return ctx.to_dict()





@task.external_python(python="{{ params.venv_python }}",retries=3)
def download_raw_data(ctx, split_name):
        
    from addict import Dict
    from tqdm import tqdm
    import requests
    import os
    import os.path as osp

    def download(url: str, fname: str):
        try:
            resp = requests.get(url, stream=True, timeout =5)
            total = int(resp.headers.get('content-length', 0))
                    # Can also replace 'file' with a io.BytesIO object
            with open(fname, 'wb') as file, tqdm(
                        desc=fname,
                        total=total,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as bar:
                for data in resp.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)
            return True
        except requests.exceptions.ConnectionError:
            return False


    ctx=Dict(ctx)
    raw_data_folder=osp.join(ctx.run.pipeline_tmp_folder,'raw_data')
    os.makedirs(raw_data_folder, exist_ok =ctx.run.keep_folder)

    url=f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{ctx.data[split_name].date.year}-{ctx.data[split_name].date.month:02}.parquet'
    output_file=osp.join(raw_data_folder,f"{split_name}.parquet")
    print(split_name, url)
    
    if not (ctx.run.keep_folder and osp.isfile(output_file) ):
        assert download(url, output_file), f'download failed of {url}'
    ctx.data[split_name].raw_file=output_file
    return ctx.to_dict()




@task.external_python(python="{{ params.venv_python }}")
def prepare_data(ctx):

    from addict import Dict
    import pandas as pd
    import os
    import os.path as osp
    import mlflow

    ctx=Dict(ctx)
    prepared_data_folder=osp.join(ctx.run.pipeline_tmp_folder,'prep_data')
    os.makedirs(prepared_data_folder, exist_ok =ctx.run.keep_folder)

    mlflow.set_tracking_uri(ctx.run.mlflow_tracking_url)
    mlflow.set_experiment(ctx.run.mlflow_experiment_name)

    for  split_name in ctx.data:

        print(split_name)

        df = pd.read_parquet(ctx.data[split_name].raw_file)
            
        print(f'{split_name}: raw: {df.shape}')

        with mlflow.start_run(run_id=ctx.run.mlflow.run_id):
            mlflow.log_param(f'{split_name}_init_shape',df.shape)

        df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
        df.duration = df.duration.dt.total_seconds() / 60.0

        df = df[(df.duration >= 1.0) & (df.duration <= 60.0)]

        categorical = ['PULocationID', 'DOLocationID']
        df[categorical] = df[categorical].astype(str)


        print(f'{split_name}: prep: {df.shape}')

        with mlflow.start_run(run_id=ctx.run.mlflow.run_id):
            mlflow.log_param(f'{split_name}_prepared_shape',df.shape)

        ctx.data[split_name].prepared_file=\
            osp.join(prepared_data_folder,f'{split_name}.parquet')
        
        df=df.iloc[::int(1.0/ctx.data[split_name].sampling)]
        df.to_parquet( ctx.data[split_name].prepared_file)

    return ctx.to_dict()



@task.external_python(python="{{ params.venv_python }}")
def preprocess_data(ctx):

    from addict import Dict
    import os
    import os.path as osp
    import pickle
    import pandas as pd
    from  sklearn.feature_extraction import DictVectorizer
    import numpy as np
    import mlflow

    ctx=Dict(ctx)
    preprocessed_data_folder=osp.join(ctx.run.pipeline_tmp_folder,'preprocessed_data')
    os.makedirs(preprocessed_data_folder, exist_ok=ctx.run.keep_folder)

    mlflow.set_tracking_uri(ctx.run.mlflow_tracking_url)
    mlflow.set_experiment(ctx.run.mlflow_experiment_name)

    input_feats = ['PULocationID', 'DOLocationID']
    output_feat = 'duration'

    

    prepared_data={split_name:pd.read_parquet(ctx.data[split_name].prepared_file) \
                    for split_name in ctx.data}

    with mlflow.start_run(run_id=ctx.run.mlflow.run_id) as run:
        
        mlflow.sklearn.autolog()

        dict_vect=DictVectorizer(sparse=False)

        for split_name in ['train','val','test']:
            print(f'{split_name} preprocessing')
                    
            X=prepared_data[split_name][input_feats]
            X=X.to_dict(orient='records')
                    
            if split_name=='train':
                X=dict_vect.fit_transform(X)
            else:
                X=dict_vect.transform(X)
                    
            y=prepared_data[split_name][output_feat].to_numpy()

            ctx.data[split_name].preprocessed_data=osp.join(preprocessed_data_folder,
                                                    f'{split_name}.npz')
            np.savez_compressed(ctx.data[split_name].preprocessed_data,
                                        X=X,y=y)

        mlflow.sklearn.log_model(sk_model=dict_vect,
                                 artifact_path='autolog_dict_vectorizer')
        
        ctx.run.dict_vect=osp.join(ctx.run.pipeline_tmp_folder,'dict_vect.bin')
        with open(ctx.run.dict_vect,'wb') as f:
            pickle.dump(dict_vect,f)
    
    return ctx.to_dict()



@task.external_python(python="{{ params.venv_python }}")
def ml_train(ctx):
        
    
    from addict import Dict
    import time
    import os
    import os.path as osp
    import pickle

    import pandas as pd
    import numpy as np

    from  sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import root_mean_squared_error

    import mlflow


    ctx=Dict(ctx)


    mlflow.set_tracking_uri(ctx.run.mlflow_tracking_url)
    mlflow.set_experiment(ctx.run.mlflow_experiment_name)

    print('training ...')

    
    with mlflow.start_run(run_id=ctx.run.mlflow.run_id) as run:
        
        mlflow.sklearn.autolog()
        
        mlflow.log_param('train_sample',ctx.run.train_sample)

        model=LinearRegression(copy_X=False)

        with np.load(ctx.data.train.preprocessed_data) as data:
            
            X=data['X'].copy()
            y=data['y'].copy()
            print('start training')
            start = time.time()
            model.fit(X,y)
            end = time.time()
            print(f'training time: {int(end - start)} s')
            print('end training')
                
            train_rmse = root_mean_squared_error(data['y'],
                                                model.predict(data['X']))

            
        print(f'intercept: {model.intercept_}')
        print(f'train_rmse : {train_rmse}')

        mlflow.log_param('intercept_',model.intercept_)
        mlflow.log_metric('train_rmse', train_rmse)

        

        mlflow.sklearn.log_model(sk_model=model,
                                 artifact_path='autolog_model',
                                 registered_model_name=\
                                    ctx.run.mlflow_experiment_name+'-linear-model')

        ctx.run.model=osp.join(ctx.run.pipeline_tmp_folder,'model.bin')
        with open(ctx.run.model,'wb') as f:
            pickle.dump(model,f)
            
        data=np.load(ctx.data.val.preprocessed_data)
        val_rmse = root_mean_squared_error(data['y'],model.predict(data['X']))
        print(f'val_rmse : {val_rmse}')

        mlflow.log_metric('val_rmse', val_rmse)
            
        data=np.load(ctx.data.test.preprocessed_data)
        test_rmse = root_mean_squared_error(data['y'],model.predict(data['X']))
        print(f'test_rmse : {test_rmse}')

        mlflow.log_metric('test_rmse', test_rmse)

        
        return ctx.to_dict()