import os
from unittest.mock import patch, Mock
import yaml
import pytest
from click.testing import CliRunner
from fonz.tests.constants import TEST_BASE_URL
from fonz.cli import connect
import logging


@pytest.fixture(scope="class")
def runner(request):
    """Click's CLI runner to invoke commands as command line scripts."""
    request.cls.runner = CliRunner()


@pytest.mark.usefixtures("runner")
class TestConnect(object):
    def test_help(self):
        result = self.runner.invoke(
            connect, ["--help"], standalone_mode=False, catch_exceptions=False
        )
        assert result.exit_code == 0

    def test_no_arguments_exits_with_nonzero_code(self):
        result = self.runner.invoke(connect)
        assert result.exit_code != 0

    @patch("fonz.cli.Fonz", autospec=True)
    def test_with_command_line_args_only(self, mock_client):
        result = self.runner.invoke(
            connect,
            [
                "--base-url",
                TEST_BASE_URL,
                "--client-id",
                "FAKE_CLIENT_ID",
                "--client-secret",
                "FAKE_CLIENT_SECRET",
            ],
            standalone_mode=False,
            catch_exceptions=False,
        )
        mock_client.assert_called_once_with(
            TEST_BASE_URL, "FAKE_CLIENT_ID", "FAKE_CLIENT_SECRET", 19999, "3.0"
        )
        mock_client.return_value.connect.assert_called_once()
        assert result.exit_code == 0

    @patch("fonz.cli.Fonz", autospec=True)
    @patch.dict(
        os.environ,
        {
            "LOOKER_BASE_URL": TEST_BASE_URL,
            "LOOKER_CLIENT_ID": "FAKE_CLIENT_ID",
            "LOOKER_CLIENT_SECRET": "FAKE_CLIENT_SECRET",
        },
    )
    def test_with_env_vars_only(self, mock_client):
        result = self.runner.invoke(
            connect, standalone_mode=False, catch_exceptions=False
        )
        mock_client.assert_called_once_with(
            TEST_BASE_URL, "FAKE_CLIENT_ID", "FAKE_CLIENT_SECRET", 19999, "3.0"
        )
        mock_client.return_value.connect.assert_called_once()
        assert result.exit_code == 0

    @patch("fonz.cli.Fonz", autospec=True)
    def test_with_config_file_only(self, mock_client):
        with self.runner.isolated_filesystem():
            with open("config.yml", "w") as file:
                config = {
                    "base_url": TEST_BASE_URL,
                    "client_id": "FAKE_CLIENT_ID",
                    "client_secret": "FAKE_CLIENT_SECRET",
                }
                yaml.dump(config, file)
            result = self.runner.invoke(
                connect,
                ["--config-file", "config.yml"],
                standalone_mode=False,
                catch_exceptions=False,
            )
        mock_client.assert_called_once_with(
            TEST_BASE_URL, "FAKE_CLIENT_ID", "FAKE_CLIENT_SECRET", 19999, "3.0"
        )
        mock_client.return_value.connect.assert_called_once()
        assert result.exit_code == 0

    @patch("fonz.cli.Fonz", autospec=True)
    @patch.dict(os.environ, {"LOOKER_CLIENT_SECRET": "FAKE_CLIENT_SECRET"})
    def test_with_config_file_args_and_env_vars(self, mock_client):
        with self.runner.isolated_filesystem():
            with open("config.yml", "w") as file:
                config = {"client_id": "FAKE_CLIENT_ID"}
                yaml.dump(config, file)
            result = self.runner.invoke(
                connect,
                ["--base-url", TEST_BASE_URL, "--config-file", "config.yml"],
                standalone_mode=False,
                catch_exceptions=False,
            )
        mock_client.assert_called_once_with(
            TEST_BASE_URL, "FAKE_CLIENT_ID", "FAKE_CLIENT_SECRET", 19999, "3.0"
        )
        mock_client.return_value.connect.assert_called_once()
        assert result.exit_code == 0

    @patch("fonz.cli.Fonz", autospec=True)
    @patch.dict(
        os.environ,
        {"LOOKER_BASE_URL": "URL_ENV_VAR", "LOOKER_CLIENT_ID": "CLIENT_ID_ENV_VAR"},
    )
    def test_cli_supersedes_env_var_which_supersedes_config_file(self, mock_client):
        with self.runner.isolated_filesystem():
            with open("config.yml", "w") as file:
                config = {
                    "base_url": "URL_CONFIG_FILE",
                    "client_id": "CLIENT_ID_CONFIG_FILE",
                    "client_secret": "CLIENT_SECRET_CONFIG_FILE",
                }
                yaml.dump(config, file)
            result = self.runner.invoke(
                connect,
                ["--base-url", "URL_CLI", "--config-file", "config.yml"],
                standalone_mode=False,
                catch_exceptions=False,
            )
        mock_client.assert_called_once_with(
            "URL_CLI", "CLIENT_ID_ENV_VAR", "CLIENT_SECRET_CONFIG_FILE", 19999, "3.0"
        )
        mock_client.return_value.connect.assert_called_once()
        assert result.exit_code == 0
