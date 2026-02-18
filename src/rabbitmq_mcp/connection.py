"""Connection manager for RabbitMQ with SSL/CA certificate support."""

import os
import ssl
from typing import Optional, Any, List, Dict
from dataclasses import dataclass, field
from urllib.parse import quote

import httpx
import pika
from loguru import logger


@dataclass
class RabbitMQConfig:
    """RabbitMQ connection configuration from environment variables."""
    
    host: str = field(default_factory=lambda: os.getenv("RABBITMQ_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_PORT", "5672")))
    user: str = field(default_factory=lambda: os.getenv("RABBITMQ_USER", "guest"))
    password: str = field(default_factory=lambda: os.getenv("RABBITMQ_PASSWORD", "guest"))
    vhost: str = field(default_factory=lambda: os.getenv("RABBITMQ_VHOST", "/"))
    use_ssl: bool = field(default_factory=lambda: os.getenv("RABBITMQ_USE_SSL", "false").lower() == "true")
    ca_cert: Optional[str] = field(default_factory=lambda: os.getenv("RABBITMQ_CA_CERT", None))
    heartbeat: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_HEARTBEAT", "3600")))
    socket_timeout: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_SOCKET_TIMEOUT", "5")))
    management_port: int = field(default_factory=lambda: int(os.getenv("RABBITMQ_MANAGEMENT_PORT", "15672")))


class RabbitMQConnection:
    """RabbitMQ connection manager with SSL/CA certificate support."""
    
    def __init__(self, config: Optional[RabbitMQConfig] = None):
        """Initialize connection manager.
        
        Args:
            config: RabbitMQ configuration. If None, uses environment variables.
        """
        self.config = config or RabbitMQConfig()
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[Any] = None
        
    def _get_ssl_options(self) -> Optional[pika.SSLOptions]:
        """Create SSL options with CA certificate if configured."""
        if not self.config.use_ssl:
            return None
            
        ssl_context = ssl.create_default_context()
        
        if self.config.ca_cert:
            logger.info(f"Loading CA certificate from {self.config.ca_cert}")
            ssl_context.load_verify_locations(cafile=self.config.ca_cert)
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            logger.warning("SSL enabled but no CA certificate provided, using default verification")
            
        return pika.SSLOptions(
            context=ssl_context,
            server_hostname=self.config.host
        )
    
    def _get_connection_parameters(self) -> pika.ConnectionParameters:
        """Build connection parameters."""
        credentials = pika.PlainCredentials(
            username=self.config.user,
            password=self.config.password
        )
        
        return pika.ConnectionParameters(
            host=self.config.host,
            port=self.config.port,
            virtual_host=self.config.vhost,
            credentials=credentials,
            ssl_options=self._get_ssl_options(),
            heartbeat=self.config.heartbeat,
            socket_timeout=self.config.socket_timeout,
        )
    
    def connect(self) -> bool:
        """Establish connection to RabbitMQ.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            logger.info(f"Connecting to RabbitMQ at {self.config.host}:{self.config.port}")
            logger.info(f"SSL: {self.config.use_ssl}, CA cert: {self.config.ca_cert}")
            logger.info(f"VHost: {self.config.vhost}, User: {self.config.user}")
            
            self._connection = pika.BlockingConnection(self._get_connection_parameters())
            self._channel = self._connection.channel()
            logger.info("Successfully connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Close connection to RabbitMQ.
        
        Returns:
            True if disconnection successful, False otherwise.
        """
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and self._connection.is_open:
                self._connection.close()
            logger.info("Disconnected from RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
            return False
    
    @property
    def channel(self) -> Optional[Any]:
        """Get the current channel."""
        return self._channel
    
    @property
    def connection(self) -> Optional[pika.BlockingConnection]:
        """Get the current connection."""
        return self._connection
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return (
            self._connection is not None 
            and self._connection.is_open 
            and self._channel is not None 
            and self._channel.is_open
        )
    
    def ensure_connection(self) -> bool:
        """Ensure connection is active, reconnect if needed."""
        if self.is_connected():
            return True
        return self.connect()
    
    def _get_management_url(self) -> str:
        """Build Management API base URL."""
        scheme = "https" if self.config.use_ssl else "http"
        return f"{scheme}://{self.config.host}:{self.config.management_port}/api"
    
    def _get_management_client(self) -> httpx.Client:
        """Create HTTP client for Management API."""
        verify: Any = True
        if self.config.use_ssl and self.config.ca_cert:
            verify = self.config.ca_cert
        
        return httpx.Client(
            auth=(self.config.user, self.config.password),
            verify=verify,
            timeout=10.0
        )
    
    def list_queues(self) -> List[Dict[str, Any]]:
        """List all queues in the vhost via Management API.
        
        Returns:
            List of queue info dictionaries.
            
        Raises:
            httpx.HTTPError: If API request fails.
        """
        url = f"{self._get_management_url()}/queues/{quote(self.config.vhost, safe='')}"
        with self._get_management_client() as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    
    def list_exchanges(self) -> List[Dict[str, Any]]:
        """List all exchanges in the vhost via Management API.
        
        Returns:
            List of exchange info dictionaries.
            
        Raises:
            httpx.HTTPError: If API request fails.
        """
        url = f"{self._get_management_url()}/exchanges/{quote(self.config.vhost, safe='')}"
        with self._get_management_client() as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
