# **Week 3**

In this homework, I combined Airflow and MLFlow to run and log an MLOps pipeline.\
Note that we are running Airflow in standalone mode  which is just for dev and testing.


**To run the code:**
1. **Build Airflow and MLFlow docker images:**
    ```
        docker build -t airflow -f airflow.docker .
        docker build -t mlflow -f mlflow.docker .
    ```
2. **Create MLFlow and Airflow folders (store their configuration and data files)**
    ```
        mlflow:
            $HOME/mlflow_data/backend_store: backend store
            $HOME/mlflow_data/artifact_store: artifact store
        airflow:
            $HOME/airflow_data/airflow_conf: airflow  conf and dags folder
            $HOME/airflow_data/airflow_venvs: python3 virtual environment
            $HOME/airflow_data/airflow_tmp: temporary folder for the pipeline data
    ```
    Note that we used a python3 virtual environment to run the airflow dag tasks\
    and install/uninstall python packages easily without modifying the running Airflow containers.
3. **Setup the the python3 virtual environment:**
   - start a python 3.12 container in the venvs folder\
     `docker  run -it -v $HOME/airflow_data/airflow_venvs:/home/venvs python:3.12 bash`
   - Then, run the commmands in the venv_setup.txt file
4. **run docker compose:**\
   `docker compose up`
5. **copy the dag files (mlops_pipeline.py, mlops_code.py) to airflow dags folder:** `$HOME/airflow_data/airflow_conf/dags`\
if the dags folder stil does not exist, just create it.

The login credentials to the Airflow web UI are in the file `$HOME/airflow_data/airflow_conf/simple_auth_manager_passwords.json.generated`\
Now, you can run the dag from the Airflow web UI: `localhost:8080`\
Note that you can modify the dag run parameters from the UI.
The main parameters are the year and month.
The test data file corresponds to the year/month combination in the parameters.\
The val data file correponds to 1 month earlier and the train data file corresponds to 2 months earlier.

**Additional file:**
 - airflow_api_curl.txt: this file contains commands to list the dags or reparse a specific dag file using curl (Airflow REST API)
 - airflow_dag_manual_trigger.ipynb: this notebook contains code to manually trigger a dag run through Airflow REST API using the python requests package 
