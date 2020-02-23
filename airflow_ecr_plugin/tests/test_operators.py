import moto
import pytest

from airflow.models import connection
from airflow.utils import db
from airflow_ecr_plugin import operators


class TestRefreshEcrDockerConnectionOperator(object):
    @pytest.fixture(autouse=True)
    def clean_connections(self):
        with db.create_session() as session:
            session.query(connection.Connection).delete()

    @moto.mock_ecr
    def test_refersh_ecr_connection(self):
        with db.create_session() as session:
            docker_connections = (
                session.query(connection.Connection)
                .filter(connection.Connection.conn_type == "docker")
                .all()
            )

        assert len(docker_connections) == 0

        refresh_ecr_conn_operator = operators.RefreshEcrDockerConnectionOperator(
            task_id="refresh_ecr_token",
            ecr_docker_conn_id="us-east-1-ecr-conn",
            ecr_region="us-east-1",
        )

        refresh_ecr_conn_operator.execute({})

        with db.create_session() as session:
            docker_connections = (
                session.query(connection.Connection)
                .filter(connection.Connection.conn_type == "docker")
                .all()
            )

        assert len(docker_connections) == 1
        ecr_connection = docker_connections.pop()

        assert ecr_connection.conn_id == "us-east-1-ecr-conn"
        assert (
            ecr_connection.host
            == "https://012345678910.dkr.ecr.us-east-1.amazonaws.com"
        )
        assert ecr_connection.login == "AWS"
        assert ecr_connection.password == "012345678910-auth-token"

    @moto.mock_ecr
    def test_refersh_ecr_connection__existing_connection(self):
        with db.create_session() as session:
            docker_connections = (
                session.query(connection.Connection)
                .filter(connection.Connection.conn_type == "docker")
                .all()
            )
            assert len(docker_connections) == 0

            connection.Connection(
                conn_id="us-east-1-ecr-conn",
                conn_type="docker",
                host="https://012345678910.dkr.ecr.us-east-1.amazonaws.com",
                login="AWS",
                password="password",
            )

        refresh_ecr_conn_operator = operators.RefreshEcrDockerConnectionOperator(
            task_id="refresh_ecr_token",
            ecr_docker_conn_id="us-east-1-ecr-conn",
            ecr_region="us-east-1",
        )

        refresh_ecr_conn_operator.execute({})

        with db.create_session() as session:
            docker_connections = (
                session.query(connection.Connection)
                .filter(connection.Connection.conn_type == "docker")
                .all()
            )

        assert len(docker_connections) == 1
        ecr_connection = docker_connections.pop()

        assert ecr_connection.conn_id == "us-east-1-ecr-conn"
        assert (
            ecr_connection.host
            == "https://012345678910.dkr.ecr.us-east-1.amazonaws.com"
        )
        assert ecr_connection.login == "AWS"
        assert ecr_connection.password == "012345678910-auth-token"
