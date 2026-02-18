"""RabbitMQ MCP Server for ALT QA Tools."""

from .server import app, main
from .connection import RabbitMQConnection, RabbitMQConfig

__version__ = "1.0.0"
__all__ = ["app", "main", "RabbitMQConnection", "RabbitMQConfig"]
