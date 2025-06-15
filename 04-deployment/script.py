import pickle
import pandas as pd
import fire
import requests
from tqdm import tqdm

def download(url, fname):
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

def read_data(filename,
              categorical = ['PULocationID', 'DOLocationID']):
    df = pd.read_parquet(filename)

    df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')

    return df


def predict(df,
            dict_vectorizer,
            model,
            categorical = ['PULocationID', 'DOLocationID']):
    dicts = df[categorical].to_dict(orient='records')
    X_val = dict_vectorizer.transform(dicts)
    y_pred = model.predict(X_val)
    return y_pred


def run(model_path='model.bin',
        year=2023,
        month=3,
        output_file='output.parquet'):

    with open(model_path, 'rb') as f_in:
        dv, model = pickle.load(f_in)

    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year:04d}-{month:02d}.parquet'
    saved_file_path=url.split('/')[-1]

    print('downloading file ...')
    assert download(url,saved_file_path), 'download failed!'

    df = read_data(saved_file_path)

    df['duration_prediction']=predict(df,
                                      dv,
                                      model)

    print(f'predicted duration mean: {df["duration_prediction"].mean()}')
    print(f'predicted duration std: {df["duration_prediction"].std()}')
    
    df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')
    df_result=df[ ['ride_id','duration_prediction'] ]

    df_result.to_parquet(
        output_file,
        engine='pyarrow',
        compression=None,
        index=False
    )

if __name__=='__main__':
    fire.Fire(run)


