import moto

from airflow_ecr_plugin import hooks


class TestAwsEcrHook(object):
    @moto.mock_ecr
    def test_get_auth_data__default_registry(self):
        ecr_hook = hooks.AwsEcrHook(region_name="us-east-2")
        auth_data = ecr_hook.get_auth_data()

        assert auth_data.username == "AWS"
        assert auth_data.password == "012345678910-auth-token"

    @moto.mock_ecr
    def test_get_auth_data__with_registryid(self):
        ecr_hook = hooks.AwsEcrHook(region_name="us-east-2")
        auth_data = ecr_hook.get_auth_data(registry_id="myregistry")

        assert auth_data.username == "AWS"
        assert auth_data.password == "myregistry-auth-token"
