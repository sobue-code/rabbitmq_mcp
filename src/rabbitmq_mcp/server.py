"""RabbitMQ MCP Server for ALT QA Tools.

A Model Context Protocol server that provides RabbitMQ operations
with full SSL/CA certificate support.
"""

import json
import sys
from typing import Optional, List, Dict, Any

import pika
from pika.exceptions import ChannelClosedByBroker, AMQPError
from loguru import logger

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .connection import RabbitMQConnection, RabbitMQConfig


# Configure logger
logger.remove()
logger.add(sys.stderr, level="WARNING", format="{time} | {level} | {message}")


# Create MCP server instance
app = Server("rabbitmq-mcp-altqa")

# Global connection manager (initialized from env vars)
_connection_manager: Optional[RabbitMQConnection] = None


def get_connection() -> RabbitMQConnection:
    """Get or create the global connection manager."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = RabbitMQConnection()
    return _connection_manager


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available RabbitMQ tools."""
    return [
        Tool(
            name="rabbitmq_connect",
            description="Connect to RabbitMQ broker using environment variables. " +
                       "Set RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD, " +
                       "RABBITMQ_VHOST, RABBITMQ_USE_SSL, RABBITMQ_CA_CERT before calling.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="rabbitmq_disconnect",
            description="Disconnect from RabbitMQ broker.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="rabbitmq_status",
            description="Check connection status to RabbitMQ broker.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="rabbitmq_list_queues",
            description="List all queues in the connected vhost using Management API.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="rabbitmq_list_exchanges",
            description="List all exchanges in the connected vhost using Management API.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="rabbitmq_declare_queue",
            description="Declare a new queue. Creates quorum queue by default.",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue to declare"
                    },
                    "durable": {
                        "type": "boolean",
                        "description": "Whether the queue should survive broker restart",
                        "default": True
                    },
                    "exclusive": {
                        "type": "boolean",
                        "description": "Whether the queue should be exclusive",
                        "default": False
                    },
                    "auto_delete": {
                        "type": "boolean", 
                        "description": "Whether to auto-delete when unused",
                        "default": False
                    },
                    "queue_type": {
                        "type": "string",
                        "description": "Queue type: 'quorum' or 'classic'",
                        "enum": ["quorum", "classic"],
                        "default": "quorum"
                    }
                },
                "required": ["queue_name"]
            }
        ),
        Tool(
            name="rabbitmq_delete_queue",
            description="Delete a queue from the vhost.",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue to delete"
                    },
                    "if_unused": {
                        "type": "boolean",
                        "description": "Only delete if queue has no consumers",
                        "default": False
                    },
                    "if_empty": {
                        "type": "boolean",
                        "description": "Only delete if queue is empty",
                        "default": False
                    }
                },
                "required": ["queue_name"]
            }
        ),
        Tool(
            name="rabbitmq_purge_queue",
            description="Remove all messages from a queue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue to purge"
                    }
                },
                "required": ["queue_name"]
            }
        ),
        Tool(
            name="rabbitmq_declare_exchange",
            description="Declare a new exchange.",
            inputSchema={
                "type": "object",
                "properties": {
                    "exchange_name": {
                        "type": "string",
                        "description": "Name of the exchange to declare"
                    },
                    "exchange_type": {
                        "type": "string",
                        "description": "Exchange type: direct, topic, fanout, headers",
                        "enum": ["direct", "topic", "fanout", "headers"],
                        "default": "topic"
                    },
                    "durable": {
                        "type": "boolean",
                        "description": "Whether the exchange should survive broker restart",
                        "default": True
                    }
                },
                "required": ["exchange_name"]
            }
        ),
        Tool(
            name="rabbitmq_delete_exchange",
            description="Delete an exchange.",
            inputSchema={
                "type": "object",
                "properties": {
                    "exchange_name": {
                        "type": "string",
                        "description": "Name of the exchange to delete"
                    },
                    "if_unused": {
                        "type": "boolean",
                        "description": "Only delete if exchange has no bindings",
                        "default": False
                    }
                },
                "required": ["exchange_name"]
            }
        ),
        Tool(
            name="rabbitmq_bind_queue",
            description="Bind a queue to an exchange with a routing key.",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue to bind"
                    },
                    "exchange_name": {
                        "type": "string",
                        "description": "Name of the exchange to bind to"
                    },
                    "routing_key": {
                        "type": "string",
                        "description": "Routing key for the binding"
                    }
                },
                "required": ["queue_name", "exchange_name", "routing_key"]
            }
        ),
        Tool(
            name="rabbitmq_unbind_queue",
            description="Unbind a queue from an exchange.",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue to unbind"
                    },
                    "exchange_name": {
                        "type": "string",
                        "description": "Name of the exchange to unbind from"
                    },
                    "routing_key": {
                        "type": "string",
                        "description": "Routing key for the binding"
                    }
                },
                "required": ["queue_name", "exchange_name", "routing_key"]
            }
        ),
        Tool(
            name="rabbitmq_publish",
            description="Publish a message to an exchange with a routing key.",
            inputSchema={
                "type": "object",
                "properties": {
                    "exchange_name": {
                        "type": "string",
                        "description": "Name of the exchange to publish to (empty string for default)"
                    },
                    "routing_key": {
                        "type": "string",
                        "description": "Routing key for the message"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message body (will be sent as-is, JSON strings should be pre-formatted)"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Content type of the message",
                        "default": "application/json"
                    }
                },
                "required": ["exchange_name", "routing_key", "message"]
            }
        ),
        Tool(
            name="rabbitmq_publish_to_queue",
            description="Publish a message directly to a queue (using default exchange).",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue to publish to"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message body"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Content type of the message",
                        "default": "application/json"
                    }
                },
                "required": ["queue_name", "message"]
            }
        ),
        Tool(
            name="rabbitmq_get_message",
            description="Get a single message from a queue (non-destructive peek, or with ack).",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue to get message from"
                    },
                    "auto_ack": {
                        "type": "boolean",
                        "description": "If true, message is removed from queue",
                        "default": False
                    }
                },
                "required": ["queue_name"]
            }
        ),
        Tool(
            name="rabbitmq_queue_message_count",
            description="Get the number of messages in a queue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "queue_name": {
                        "type": "string",
                        "description": "Name of the queue"
                    }
                },
                "required": ["queue_name"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    conn = get_connection()
    
    try:
        # Connection management
        if name == "rabbitmq_connect":
            if conn.connect():
                config = conn.config
                return [TextContent(
                    type="text",
                    text=f"Successfully connected to RabbitMQ\n"
                         f"  Host: {config.host}:{config.port}\n"
                         f"  VHost: {config.vhost}\n"
                         f"  SSL: {config.use_ssl}\n"
                         f"  CA Cert: {config.ca_cert or 'Not specified'}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text="Failed to connect to RabbitMQ. Check logs and environment variables."
                )]
        
        elif name == "rabbitmq_disconnect":
            conn.disconnect()
            return [TextContent(type="text", text="Disconnected from RabbitMQ")]
        
        elif name == "rabbitmq_status":
            if conn.is_connected():
                config = conn.config
                return [TextContent(
                    type="text",
                    text=f"Connected to RabbitMQ\n"
                         f"  Host: {config.host}:{config.port}\n"
                         f"  VHost: {config.vhost}\n"
                         f"  SSL: {config.use_ssl}"
                )]
            else:
                return [TextContent(type="text", text="Not connected to RabbitMQ")]
        
        # All other operations require connection
        if not conn.ensure_connection():
            return [TextContent(
                type="text", 
                text="Not connected to RabbitMQ. Call rabbitmq_connect first."
            )]
        
        channel = conn.channel
        
        if name == "rabbitmq_list_queues":
            try:
                queues = conn.list_queues()
                if not queues:
                    return [TextContent(type="text", text="No queues found in vhost.")]
                
                lines = ["Queues in vhost:\n"]
                for q in queues:
                    lines.append(f"  {q['name']}")
                    lines.append(f"    Type: {q.get('type', 'classic')}")
                    lines.append(f"    Messages: {q.get('messages', 0)}")
                    lines.append(f"    Consumers: {q.get('consumers', 0)}")
                    lines.append(f"    Durable: {q.get('durable', False)}")
                    lines.append("")
                return [TextContent(type="text", text="\n".join(lines))]
            except Exception as e:
                return [TextContent(type="text", text=f"Failed to list queues: {str(e)}")]
        
        elif name == "rabbitmq_list_exchanges":
            try:
                exchanges = conn.list_exchanges()
                if not exchanges:
                    return [TextContent(type="text", text="No exchanges found in vhost.")]
                
                lines = ["Exchanges in vhost:\n"]
                for ex in exchanges:
                    name = ex.get('name', '')
                    if name:
                        lines.append(f"  {name}")
                        lines.append(f"    Type: {ex.get('type', 'direct')}")
                        lines.append(f"    Durable: {ex.get('durable', False)}")
                        lines.append("")
                return [TextContent(type="text", text="\n".join(lines))]
            except Exception as e:
                return [TextContent(type="text", text=f"Failed to list exchanges: {str(e)}")]
        
        elif name == "rabbitmq_declare_queue":
            queue_name = arguments["queue_name"]
            durable = arguments.get("durable", True)
            exclusive = arguments.get("exclusive", False)
            auto_delete = arguments.get("auto_delete", False)
            queue_type = arguments.get("queue_type", "quorum")
            
            arguments_dict = {"x-queue-type": queue_type}
            result = channel.queue_declare(
                queue=queue_name,
                durable=durable,
                exclusive=exclusive,
                auto_delete=auto_delete,
                passive=False,
                arguments=arguments_dict
            )
            return [TextContent(
                type="text",
                text=f"Queue '{queue_name}' declared successfully\n"
                     f"  Messages: {result.method.message_count}\n"
                     f"  Consumers: {result.method.consumer_count}"
            )]
        
        elif name == "rabbitmq_delete_queue":
            queue_name = arguments["queue_name"]
            if_unused = arguments.get("if_unused", False)
            if_empty = arguments.get("if_empty", False)
            
            channel.queue_delete(
                queue=queue_name,
                if_unused=if_unused,
                if_empty=if_empty
            )
            return [TextContent(type="text", text=f"Queue '{queue_name}' deleted")]
        
        elif name == "rabbitmq_purge_queue":
            queue_name = arguments["queue_name"]
            channel.queue_purge(queue=queue_name)
            return [TextContent(type="text", text=f"Queue '{queue_name}' purged")]
        
        # Exchange operations
        elif name == "rabbitmq_declare_exchange":
            exchange_name = arguments["exchange_name"]
            exchange_type = arguments.get("exchange_type", "topic")
            durable = arguments.get("durable", True)
            
            channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=durable
            )
            return [TextContent(
                type="text", 
                text=f"Exchange '{exchange_name}' declared (type: {exchange_type})"
            )]
        
        elif name == "rabbitmq_delete_exchange":
            exchange_name = arguments["exchange_name"]
            if_unused = arguments.get("if_unused", False)
            
            channel.exchange_delete(exchange=exchange_name, if_unused=if_unused)
            return [TextContent(type="text", text=f"Exchange '{exchange_name}' deleted")]
        
        # Binding operations
        elif name == "rabbitmq_bind_queue":
            queue_name = arguments["queue_name"]
            exchange_name = arguments["exchange_name"]
            routing_key = arguments["routing_key"]
            
            channel.queue_bind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key
            )
            return [TextContent(
                type="text",
                text=f"Queue '{queue_name}' bound to exchange '{exchange_name}' "
                     f"with routing key '{routing_key}'"
            )]
        
        elif name == "rabbitmq_unbind_queue":
            queue_name = arguments["queue_name"]
            exchange_name = arguments["exchange_name"]
            routing_key = arguments["routing_key"]
            
            channel.queue_unbind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key
            )
            return [TextContent(
                type="text",
                text=f"Queue '{queue_name}' unbound from exchange '{exchange_name}'"
            )]
        
        # Publishing
        elif name == "rabbitmq_publish":
            exchange_name = arguments["exchange_name"]
            routing_key = arguments["routing_key"]
            message = arguments["message"]
            content_type = arguments.get("content_type", "application/json")
            
            properties = pika.BasicProperties(content_type=content_type)
            channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message.encode('utf-8'),
                properties=properties
            )
            return [TextContent(
                type="text",
                text=f"Message published to exchange '{exchange_name}' "
                     f"with routing key '{routing_key}'"
            )]
        
        elif name == "rabbitmq_publish_to_queue":
            queue_name = arguments["queue_name"]
            message = arguments["message"]
            content_type = arguments.get("content_type", "application/json")
            
            properties = pika.BasicProperties(content_type=content_type)
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message.encode('utf-8'),
                properties=properties
            )
            return [TextContent(
                type="text",
                text=f"Message published directly to queue '{queue_name}'"
            )]
        
        # Consuming
        elif name == "rabbitmq_get_message":
            queue_name = arguments["queue_name"]
            auto_ack = arguments.get("auto_ack", False)
            
            method, properties, body = channel.basic_get(
                queue=queue_name,
                auto_ack=auto_ack
            )
            
            if method is None:
                return [TextContent(type="text", text=f"No messages in queue '{queue_name}'")]
            
            try:
                body_str = body.decode('utf-8')
                # Try to parse as JSON for pretty printing
                try:
                    parsed = json.loads(body_str)
                    body_str = json.dumps(parsed, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
            except UnicodeDecodeError:
                body_str = f"<binary data, {len(body)} bytes>"
            
            result = f"Message from queue '{queue_name}':\n"
            result += f"  Delivery tag: {method.delivery_tag}\n"
            result += f"  Exchange: {method.exchange}\n"
            result += f"  Routing key: {method.routing_key}\n"
            result += f"  Content type: {properties.content_type}\n"
            result += f"  Auto-ack: {auto_ack}\n"
            result += f"  Body:\n{body_str}"
            
            return [TextContent(type="text", text=result)]
        
        elif name == "rabbitmq_queue_message_count":
            queue_name = arguments["queue_name"]
            
            # Use passive=True to just check queue without declaring
            result = channel.queue_declare(queue=queue_name, passive=True)
            return [TextContent(
                type="text",
                text=f"Queue '{queue_name}':\n"
                     f"  Messages: {result.method.message_count}\n"
                     f"  Consumers: {result.method.consumer_count}"
            )]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except ChannelClosedByBroker as e:
        return [TextContent(
            type="text",
            text=f"RabbitMQ error: {e.reply_text} (code {e.reply_code})"
        )]
    except AMQPError as e:
        return [TextContent(type="text", text=f"AMQP error: {str(e)}")]
    except Exception as e:
        logger.exception(f"Error in tool {name}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


def main():
    """Run the MCP server."""
    import asyncio
    
    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
