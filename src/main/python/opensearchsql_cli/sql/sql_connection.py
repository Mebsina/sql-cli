"""
SQL Library Connection Management

Handles connection to SQL library and OpenSearch Cluster configuration.
"""

from py4j.java_gateway import JavaGateway, GatewayParameters
import sys
from rich.console import Console
from .sql_library_process import sql_library_manager
from .verify_cluster import VerifyCluster
from ..config.config import config_manager

# Create a console instance for rich formatting
console = Console()


class SqlConnection:
    """
    SqlConnection class for managing SQL library and OpenSearch connections
    """

    def __init__(self, port=25333):
        """
        Initialize a Connection instance

        Args:
            port: Gateway port (default 25333)
        """
        self.gateway_port = port
        self.sql_lib = None
        self.sql_connected = False
        self.opensearch_connected = False
        self.error_message = None

        # Connection parameters
        self.host = None
        self.port_num = None
        self.protocol = "http"
        self.username = None
        self.password = None

    def connect(self):
        """
        Connect to the SQL library

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Start the SQL Library server if it's not already running
            with console.status("Creating SQL Library connection...", spinner="dots"):
                if not sql_library_manager.started:
                    if not sql_library_manager.start():
                        console.print(
                            "[bold red]Failed to connect SQL Library[/bold red]"
                        )
                        return False

                # Connect to the SQL Library
                self.sql_lib = JavaGateway(
                    gateway_parameters=GatewayParameters(port=self.gateway_port)
                )
                self.sql_connected = True
                return True
        except Exception as e:
            console.print(
                f"[bold red]Failed to connect to SQL on port {self.gateway_port}: {e}[/bold red]"
            )
            self.sql_connected = False
            return False

    def initialize_opensearch(
        self, host_port=None, credentials=None, ignore_ssl=False, aws_auth=False
    ):
        """
        Initialize OpenSearch Cluster connection in the SQL library

        Args:
            host_port: Optional host:port string for OpenSearch Cluster connection
            credentials: Optional username:password string for authentication
            ignore_ssl: Whether to ignore SSL certificate validation
            aws_auth: Whether to use AWS SigV4 authentication

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sql_connected or not self.sql_lib:
            console.print(
                "[bold red]ERROR:[/bold red] Unable to connect the SQL library"
            )
            return False

        try:
            # Parse credentials if provided
            if credentials and ":" in credentials:
                self.username, self.password = credentials.split(":", 1)

            # Store original host_port for Java connection
            original_host_port = host_port if host_port else ""

            if aws_auth:
                # AWS SigV4 authentication
                if not host_port:
                    console.print(
                        "[bold red]ERROR:[/bold red] [red]URL is required for AWS Authentication[/red]"
                    )
                    return False

                # Remove protocol prefix if present
                if "://" in host_port:
                    self.protocol, host_port = host_port.split("://", 1)

                # Store the AWS host
                self.host = host_port

                # Verify AWS connection
                success, message, version, url, region = (
                    VerifyCluster.verify_aws_opensearch_connection(host_port)
                )
                if not success:
                    self.opensearch_connected = False
                    self.error_message = message
                    return False

                # Store connection information
                self.version = version
                self.url = url
                self.username = (
                    f"AWS {region}"  # Use region as the "username" for AWS connections
                )

                # If verification succeeded, initialize the connection in Java
                result = self.sql_lib.entry_point.initializeAwsConnection(host_port)
            elif host_port:
                # Handle URLs with protocol
                if "://" in host_port:
                    self.protocol, host_port = host_port.split("://", 1)

                # Parse host and port
                if ":" in host_port:
                    self.host, port_str = host_port.split(":", 1)
                    try:
                        self.port_num = int(port_str)
                    except ValueError:
                        console.print(
                            f"[bold red]ERROR:[/bold red] [red]Invalid port: {port_str}[/red]"
                        )
                        self.opensearch_connected = False
                        return False
                else:
                    self.host = host_port

                # Verify connection using parsed values
                success, message, version, url, username = (
                    VerifyCluster.verify_opensearch_connection(
                        self.host,
                        self.port_num,
                        self.protocol,
                        self.username,
                        self.password,
                        ignore_ssl,
                    )
                )
                if not success:
                    self.opensearch_connected = False
                    self.error_message = message
                    return False

                # Store connection information
                self.version = version
                self.url = url
                if username:
                    self.username = username

                # If verification succeeded, initialize the connection in Java
                result = self.sql_lib.entry_point.initializeConnection(
                    self.host,
                    self.port_num,
                    self.protocol,
                    self.username,
                    self.password,
                    ignore_ssl,
                )
            else:
                # Use default values
                success, message, version, url, username = (
                    VerifyCluster.verify_opensearch_connection(
                        self.host,
                        self.port_num,
                        self.protocol,
                        self.username,
                        self.password,
                        ignore_ssl,
                    )
                )
                if not success:
                    self.opensearch_connected = False
                    self.error_message = message
                    return False

                # Store connection information
                self.version = version
                self.url = url
                if username:
                    self.username = username

                # If verification succeeded, initialize the connection in Java
                result = self.sql_lib.entry_point.initializeConnection(
                    self.host,
                    self.port_num,
                    self.protocol,
                    self.username,
                    self.password,
                    ignore_ssl,
                )

            # Check for successful initialization
            if "Connection initialized" in result or "Already initialized" in result:
                self.opensearch_connected = True
                return True

            # Check for specific error conditions
            if "Error:" in result:
                self.error_message = result
                self.opensearch_connected = False
                return False

            self.opensearch_connected = True
            return True

        except Exception as e:
            self.error_message = f"Unable to connect to {host_port}: {str(e)}"
            self.opensearch_connected = False
            return False

    def query_executor(self, query: str, is_ppl: bool = True, format: str = "json"):
        """
        Execute a query through the SQL Library service

        Args:
            query: The SQL or PPL query string
            is_ppl: True if the query is PPL, False if SQL (default: True)
            format: Output format (json, table, csv) (default: json)

        Returns:
            Query result string formatted according to the specified format
        """
        if not self.sql_connected or not self.sql_lib:
            console.print(
                "[bold red]ERROR:[/bold red] [red]Unable to connect to SQL library[/red]"
            )
            return "Error: Not connected to SQL library"

        if not self.opensearch_connected:
            console.print(
                "[bold red]ERROR:[/bold red] [red]Unable to connect to OpenSearch Cluster[/bold red]"
            )
            return "Error: Not connected to OpenSearch Cluster"

        query_service = self.sql_lib.entry_point
        # queryExecution inside of Gateway.java
        result = query_service.queryExecution(query, is_ppl, format)
        return result

    def disconnect(self):
        """
        Notify SQL Library that OpenSearch CLI is disconnecting

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.sql_connected and self.sql_lib:
                result = self.sql_lib.entry_point.disconnect()
                self.sql_connected = False
                self.opensearch_connected = False

                return True
        except Exception as e:
            console.print(f"[bold red]Disconnect ERROR:[/bold red] [red]{e}[/red]")
            return False
        return False


# Create a global connection instance
sql_connection = SqlConnection()
