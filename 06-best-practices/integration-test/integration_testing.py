import os
import pandas as pd
from datetime import datetime

import sys
sys.path.insert(0, '..')

import batch

def dt(hour, minute, second=0):
    return datetime(2023, 1, 1, hour, minute, second)


def test_save_data():

    data = [
        (None, None, dt(1, 1), dt(1, 10)),
        (1, 1, dt(1, 2), dt(1, 10)),
        (1, None, dt(1, 2, 0), dt(1, 2, 59)),
        (3, 4, dt(1, 2, 0), dt(2, 2, 1)),      
    ]

    columns = ['PULocationID', 'DOLocationID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime']
    df = pd.DataFrame(data, columns=columns)


    input_path=batch.get_input_path(year=2023,
                                    month=1)
    print(input_path)
    batch.save_data(df, output_path=input_path)


def test_read_data():

    input_path=batch.get_input_path(year=2023,
                                    month=1)
    print(input_path)

    batch.read_data(input_path)
