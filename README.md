# Airflow AWS ECR Plugin

[![Build Status](https://travis-ci.org/asandeep/airflow-ecr-plugin.svg?branch=master)](https://travis-ci.org/asandeep/airflow-ecr-plugin)
[![codecov](https://codecov.io/gh/asandeep/airflow-ecr-plugin/branch/master/graph/badge.svg)](https://codecov.io/gh/asandeep/airflow-ecr-plugin)
[![Python Versions](https://img.shields.io/pypi/pyversions/airflow-ecr-plugin.svg)](https://pypi.org/project/airflow-ecr-plugin/)
[![Package Version](https://img.shields.io/pypi/v/airflow-ecr-plugin.svg)](https://pypi.org/project/airflow-ecr-plugin/)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This plugin exposes an operator that refreshes ECR login token at regular intervals.

## About

[Amazon ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html) is a AWS managed Docker registry to host private Docker container images. Access to Docker repositories hosted on ECR can be controlled with resource based permissions using AWS IAM.

To push/pull images, Docker client must authenticate to ECR registry as an AWS user. An authorization token can be generated using AWS CLI `get-login-password` command that can be passed to `docker login` command to authenticate to ECR registry. For instructions on setting up ECR and obtaining login token to authenticate Docker client, click [here](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html).

The authorization token obtained using `get-login-password` command is only valid for 12 hours and Docker client needs to authenticate with fresh token after every 12 hours to make sure it can access Docker images hosted on ECR. Moreover, ECR registries are region specific and separate token should be obtained to authenticate to each registry.

The whole process can be quite cumbersome when combined with Apache Airflow. Airflow's `DockerOperator` accepts `docker_conn_id` parameter that it uses to authenticate and pull images from private repositories. In case this private registry is ECR, a connection can be created with login token obtained from `get-login-password` command and the corresponding ID can be passed to `DockerOperator`. However, since the token is only valid for 12 hours, `DockerOperator` will fail to fetch images from ECR once token is expired.

This plugin implements `RefreshEcrDockerConnectionOperator` Airflow operator that can automatically update the ECR login token at regular intervals.

## Installation

#### Pypi

```bash
pip install airflow-ecr-plugin
```

#### Poetry

```bash
poetry add airflow-ecr-plugin@latest
```

## Getting Started

Once installed, plugin can be loaded via [setuptools entrypoint](https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata) mechanism.

Update your package's setup.py as below:

```python
from setuptools import setup

setup(
    name="my-package",
    ...
    entry_points = {
        'airflow.plugins': [
            'aws_ecr = airflow_ecr_plugin:AwsEcrPlugin'
        ]
    }
)
```

If you are using Poetry, plugin can be loaded by adding it under `[tool.poetry.plugin."airflow.plugins"]` section as below:

```toml
[tool.poetry.plugins."airflow.plugins"]
"aws_ecr" = "airflow_ecr_plugin:AwsEcrPlugin"
```

Once plugin is loaded, same will be available for import in python modules.

Now create a DAG to refresh ECR tokens,

```python
from datetime import timedelta

import airflow
from airflow.operators import aws_ecr


DEFAULT_ARGS = {
    "depends_on_past": False,
    "retries": 0,
    "owner": "airflow",
}

REFRESH_ECR_TOKEN_DAG = airflow.DAG(
    dag_id="Refresh_ECR_Login_Token",
    description=(
        "Fetches the latest token from ECR and updates the docker "
        "connection info."
    ),
    default_args=DEFAULT_ARGS,
    schedule_interval=<token_refresh_interval>,
    # Set start_date to past date to make sure airflow picks up the tasks for
    # execution.
    start_date=airflow.utils.dates.days_ago(2),
    catchup=False,
)

# Add below operator for each ECR connection to be refreshed.
aws_ecr.RefreshEcrDockerConnectionOperator(
    task_id=<task_id>,
    ecr_docker_conn_id=<docker_conn_id>,
    ecr_region=<ecr_region>,
    aws_conn_id=<aws_conn_id>,
    dag=REFRESH_ECR_TOKEN_DAG,
)
```

Placeholder parameters in above code snippet are defined below:

- `token_refresh_interval`: Time interval to refresh ECR login tokens. This should be less than 12 hours to prevent any access issues.
- `task_id`: Unique ID for this task.
- `docker_conn_id`: The Airflow Docker connection ID corresponding to ECR registry, that will be updated when this operator runs. The same connection ID should be passed to `DockerOperator` that pulls image from ECR registry. If connection does not exist in Airflow DB, operator will automatically create it.
- `ecr_region`: AWS region of ECR registry.
- `aws_conn_id`: Airflow connection ID corresponding to AWS user credentials that will be used to authenticate and retrieve new login token from ECR. This user should at minimum have `ecr:GetAuthorizationToken` permissions.

## Known Issues

If you are running Airflow v1.10.7 or earlier, the operator will fail due to: [AIRFLOW-3014](https://issues.apache.org/jira/browse/AIRFLOW-3014).

The work around is to update Airflow `connection` table `password` column length to 5000 characters.

## Acknowledgements

The operator is inspired from [Brian Campbell](https://www.linkedin.com/in/bvcampbell3)'s post on [Using Airflow's Docker operator with ECR](https://www.lucidchart.com/techblog/2019/03/22/using-apache-airflows-docker-operator-with-amazons-container-repository/).
