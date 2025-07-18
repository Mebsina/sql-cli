"""
Tests for verify_cluster.py

This module contains tests for the VerifyCluster class that handles
verification of connections to OpenSearch clusters.
"""

import pytest
from unittest.mock import patch, MagicMock
from opensearchsql_cli.sql.verify_cluster import VerifyCluster


class TestVerifyCluster:
    """
    Test class for VerifyCluster functionality.
    """

    @pytest.mark.parametrize(
        "test_id, description, "
        "host, port, protocol, "
        "username, password, ignore_ssl, "
        "mock_status_code, mock_json_data, "
        "expected_success, expected_message",
        [
            # HTTP Tests
            (
                1,
                "HTTP success",
                "localhost",
                9200,
                "http",
                None,
                None,
                False,
                200,
                {"version": {"number": "2.0.0"}},
                True,
                "success",
            ),
            (
                2,
                "HTTP fail host:port",
                "invalid-host",
                9200,
                "http",
                None,
                None,
                False,
                None,
                None,
                False,
                "Unable to connect http://invalid-host:9200",
            ),
            # HTTPS Tests
            (
                3,
                "HTTPS success with auth",
                "localhost",
                9200,
                "https",
                "admin",
                "admin",
                False,
                200,
                {"version": {"number": "2.0.0"}},
                True,
                "success",
            ),
            (
                4,
                "HTTPS fail with no auth provided",
                "localhost",
                9200,
                "https",
                None,
                None,
                False,
                401,
                None,
                False,
                "Unautorized 401 please verify your username/password.",
            ),
            (
                5,
                "HTTPS fail with incorrect auth",
                "localhost",
                9200,
                "https",
                "wrong",
                "wrong",
                False,
                401,
                None,
                False,
                "Unautorized 401 please verify your username/password.",
            ),
            (
                6,
                "HTTPS success with insecure flag",
                "localhost",
                9200,
                "https",
                "admin",
                "admin",
                True,
                200,
                {"version": {"number": "2.0.0"}},
                True,
                "success",
            ),
            (
                7,
                "HTTPS fail with SSL error",
                "localhost",
                9200,
                "https",
                None,
                None,
                False,
                None,
                None,
                False,
                "Unable to verify SSL Certificate. Try adding -k flag",
            ),
        ],
    )
    @patch("opensearchsql_cli.sql.verify_cluster.requests.get")
    def test_verify_opensearch_connection(
        self,
        mock_get,
        test_id,
        description,
        host,
        port,
        protocol,
        username,
        password,
        ignore_ssl,
        mock_status_code,
        mock_json_data,
        expected_success,
        expected_message,
    ):
        """
        Test the verify_opensearch_connection method for different scenarios.
        """

        print(f"\n=== Test #{test_id}: {description} ===")

        mock_response = MagicMock()
        mock_response.status_code = mock_status_code

        if mock_json_data:
            mock_response.json.return_value = mock_json_data

        if mock_status_code is None:
            # Simulate an exception
            if "SSL error" in description:
                mock_get.side_effect = Exception("SSLCertVerificationError")
            else:
                mock_get.side_effect = Exception("NewConnectionError")
        else:
            mock_get.return_value = mock_response

        # Store the input username to compare with the returned username
        input_username = username

        success, message, version, url, returned_username = (
            VerifyCluster.verify_opensearch_connection(
                host, port, protocol, username, password, ignore_ssl
            )
        )

        # Verify the results
        assert success == expected_success
        assert message == expected_message

        if expected_success:
            assert version == mock_json_data["version"]["number"]
            assert url == f"{protocol}://{host}:{port}"
            assert returned_username == input_username

        print(f"Result: {'Success' if success else 'Failure'}, Message: {message}")

    @pytest.mark.parametrize(
        "test_id, description, "
        "host, mock_credentials, mock_region, "
        "mock_status_code, mock_json_data, "
        "expected_success, expected_message",
        [
            # AWS Tests
            (
                1,
                "AWS success",
                "test-domain.us-west-2.es.amazonaws.com",
                True,
                "us-west-2",
                200,
                {"version": {"number": "2.0.0"}},
                True,
                "success",
            ),
            (
                2,
                "AWS fail with missing credential",
                "test-domain.us-west-2.es.amazonaws.com",
                False,
                "us-west-2",
                None,
                None,
                False,
                "Unable to retrieve AWS credentials.",
            ),
            (
                3,
                "AWS fail with missing region",
                "test-domain.us-west-2.es.amazonaws.com",
                True,
                None,
                None,
                None,
                False,
                "Unable to retrieve AWS region.",
            ),
            (
                4,
                "AWS fail with 403",
                "test-domain.us-west-2.es.amazonaws.com",
                True,
                "us-west-2",
                403,
                None,
                False,
                "Forbidden 403 please verify your permissions/tokens/keys.",
            ),
            (
                5,
                "AWS fail with missing key",
                "test-domain.us-west-2.es.amazonaws.com",
                True,
                "us-west-2",
                None,
                None,
                False,
                "missing AWS_SECRET_ACCESS_KEY",
            ),
        ],
    )
    @patch("opensearchsql_cli.sql.verify_cluster.requests.get")
    @patch("opensearchsql_cli.sql.verify_cluster.boto3.Session")
    def test_verify_aws_opensearch_connection(
        self,
        mock_session,
        mock_get,
        test_id,
        description,
        host,
        mock_credentials,
        mock_region,
        mock_status_code,
        mock_json_data,
        expected_success,
        expected_message,
    ):
        """
        Test the verify_aws_opensearch_connection method for different scenarios.
        """

        print(f"\n=== Test #{test_id}: {description} ===")

        session_instance = MagicMock()
        mock_session.return_value = session_instance

        # Configure credentials and region
        credentials = MagicMock() if mock_credentials else None
        session_instance.get_credentials.return_value = credentials
        session_instance.region_name = mock_region

        if credentials:
            credentials.access_key = "test_access_key"
            credentials.secret_key = "test_secret_key"
            credentials.token = "test_token"

        mock_response = MagicMock()
        mock_response.status_code = mock_status_code

        if mock_json_data:
            mock_response.json.return_value = mock_json_data

        if mock_status_code is None:
            if "missing key" in description:
                mock_get.side_effect = Exception("AWS_SECRET_ACCESS_KEY")
            else:
                mock_get.side_effect = Exception("Connection error")
        else:
            mock_get.return_value = mock_response

        success, message, version, url, region = (
            VerifyCluster.verify_aws_opensearch_connection(host)
        )

        # Verify the results
        assert success == expected_success
        assert message == expected_message

        if expected_success:
            assert version == mock_json_data["version"]["number"]
            assert url == f"https://{host}"
            assert region == mock_region

        print(f"Result: {'Success' if success else 'Failure'}, Message: {message}")
