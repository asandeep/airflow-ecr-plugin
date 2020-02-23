import base64
import json
from collections import namedtuple
from datetime import datetime

import airflow
from airflow.contrib.hooks.aws_hook import AwsHook


class ECRAuthorizationDataObject(
    namedtuple(
        "ECRAuthorizationDataObject",
        ["authorizationToken", "expiresAt", "proxyEndpoint"],
    )
):
    __slots__ = ()

    @classmethod
    def create(cls, auth_token_data):
        return cls("", None, "")._replace(**auth_token_data)

    @property
    def username(self):
        auth_token = base64.b64decode(self.authorizationToken).decode()
        return auth_token.split(":")[0]

    @property
    def password(self):
        auth_token = base64.b64decode(self.authorizationToken).decode()
        return auth_token.split(":")[1]


class AwsEcrHook(AwsHook):
    """
    Hook to interact with Amazon Elastic Container Registry.
    """

    def __init__(self, region_name, aws_conn_id="aws_default", verify=None):
        super(AwsEcrHook, self).__init__(aws_conn_id, verify)

        self._conn = self.get_client_type("ecr", region_name)

    def get_auth_data(self, registry_id=None):
        args = {}
        if registry_id:
            args["registryIds"] = [registry_id]

        response = self._conn.get_authorization_token(**args)

        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise airflow.exceptions.AirflowBadRequest(
                json.dumps(response["ResponseMetadata"])
            )

        authorization_data = response["authorizationData"].pop()
        return ECRAuthorizationDataObject.create(authorization_data)
