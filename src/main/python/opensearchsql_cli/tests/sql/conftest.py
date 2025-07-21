"""
Pytest fixtures for SQL tests.

This module contains fixtures used by the SQL tests.
"""

import pytest
import subprocess
from unittest.mock import MagicMock, PropertyMock, patch


# Fixture for verify_cluster.py
@pytest.fixture
def mock_response():
    """
    Fixture that returns a mock HTTP response.
    """
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"version": {"number": "2.0.0"}}
    return mock


@pytest.fixture
def mock_error_response():
    """
    Fixture that returns a mock HTTP error response.
    """
    mock = MagicMock()
    mock.status_code = 401
    return mock


@pytest.fixture
def mock_aws_credentials():
    """
    Fixture that returns mock AWS credentials.
    """
    mock = MagicMock()
    mock.access_key = "test_access_key"
    mock.secret_key = "test_secret_key"
    mock.token = "test_token"
    return mock


@pytest.fixture
def mock_aws_session():
    """
    Fixture that returns a mock AWS session.
    """
    mock = MagicMock()
    mock.get_credentials.return_value = mock_aws_credentials()
    mock.region_name = "us-west-2"
    return mock


# Fixtures for test_sql_library.py
@pytest.fixture
def mock_process():
    """
    Fixture that returns a mock subprocess.Popen instance.
    """
    mock = MagicMock()
    mock.stdout.readline.return_value = "Gateway Server Started"
    mock.poll.return_value = None
    return mock


@pytest.fixture
def mock_process_timeout():
    """
    Fixture that returns a mock subprocess.Popen instance that times out.
    """
    mock = MagicMock()
    mock.stdout.readline.return_value = "Some other output"
    return mock


# Fixtures for test_sql_connection.py
@pytest.fixture
def mock_java_gateway():
    """
    Fixture that returns a mock JavaGateway instance.
    """
    mock = MagicMock()
    mock.entry_point.initializeConnection.return_value = True
    mock.entry_point.initializeAwsConnection.return_value = True
    mock.entry_point.queryExecution.return_value = '{"result": "test data"}'
    return mock


@pytest.fixture
def mock_sql_library_manager():
    """
    Fixture that returns a mock SqlLibraryManager instance.
    """
    mock = MagicMock()
    mock.started = True
    mock.start.return_value = True
    return mock


@pytest.fixture
def mock_verify_cluster():
    """
    Fixture that returns a mock VerifyCluster class with static methods.
    """
    mock = MagicMock()

    # Mock the verify_opensearch_connection static method
    mock.verify_opensearch_connection.return_value = (
        True,
        "success",
        "2.0.0",
        "http://localhost:9200",
        "admin",
    )

    # Mock the verify_aws_opensearch_connection static method
    mock.verify_aws_opensearch_connection.return_value = (
        True,
        "success",
        "2.0.0",
        "https://test-domain.us-west-2.es.amazonaws.com",
        "us-west-2",
    )

    return mock
