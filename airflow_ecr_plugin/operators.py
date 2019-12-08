from airflow import models
from airflow.models import connection
from airflow.utils import db, decorators
from aws_ecr_plugin import hooks


class RefreshEcrDockerConnectionOperator(models.BaseOperator):
    @decorators.apply_defaults
    def __init__(
        self,
        ecr_docker_conn_id,
        ecr_region,
        aws_conn_id="aws_default",
        *args,
        **kwargs
    ):
        super(RefreshEcrDockerConnectionOperator, self).__init__(
            *args, **kwargs
        )

        self.ecr_docker_conn_id = ecr_docker_conn_id
        self.ecr_region = ecr_region

        self.aws_conn_id = aws_conn_id

    def execute(self, context):
        ecr_hook = hooks.AwsEcrHook(
            aws_conn_id=self.aws_conn_id, region_name=self.ecr_region
        )
        auth_token_data = ecr_hook.get_auth_data()
        self.log.debug(
            "Successfully fetched new token for region: %s", self.ecr_region
        )

        with db.create_session() as session:
            docker_connection = (
                session.query(connection.Connection)
                .filter(
                    connection.Connection.conn_id == self.ecr_docker_conn_id
                )
                .one_or_none()
            )

            if not docker_connection:
                docker_connection = connection.Connection(
                    conn_id=self.ecr_docker_conn_id,
                    conn_type="docker",
                    host=auth_token_data.proxyEndPoint,
                    login=auth_token_data.username,
                )
                session.add(docker_connection)

            docker_connection.set_password(auth_token_data.password)
            self.log.info(
                "Connection: %s refreshed with latest token. Token expiry: %s",
                self.ecr_docker_conn_id,
                auth_token_data.expiresAt,
            )
