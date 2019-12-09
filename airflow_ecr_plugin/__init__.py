from airflow import plugins_manager
from airflow_ecr_plugin import hooks, operators


class AwsEcrPlugin(plugins_manager.AirflowPlugin):
    name = "aws_ecr"

    hooks = [hooks.AwsEcrHook]
    operators = [operators.RefreshEcrDockerConnectionOperator]
