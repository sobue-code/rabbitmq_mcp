# RabbitMQ MCP Server

MCP сервер для работы с RabbitMQ с полной поддержкой SSL/CA сертификатов.

**Репозиторий:** https://github.com/sobue-code/rabbitmq_mcp

## Возможности

- Полная поддержка SSL/TLS с CA сертификатами
- Управление очередями (создание, удаление, очистка)
- Управление exchanges (создание, удаление)
- Привязка очередей к exchanges
- Публикация сообщений
- Чтение сообщений из очередей
- Проверка статуса соединения

## Установка

### Вариант 1: Из GitHub (рекомендуется)

Добавьте в конфигурацию MCP (`~/.config/opencode/opencode.json` или `.mcp.json` в проекте):

```json
{
  "mcpServers": {
    "rabbitmq": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/sobue-code/rabbitmq_mcp.git",
        "rabbitmq-mcp-altqa"
      ],
      "env": {
        "RABBITMQ_HOST": "your-rabbitmq-host.com",
        "RABBITMQ_PORT": "5671",
        "RABBITMQ_USER": "your-username",
        "RABBITMQ_PASSWORD": "your-password",
        "RABBITMQ_VHOST": "your-vhost",
        "RABBITMQ_USE_SSL": "true",
        "RABBITMQ_CA_CERT": "/path/to/your/ca_cert.pem"
      }
    }
  }
}
```

### Вариант 2: Локальная установка (для разработки)

```bash
# Клонировать репозиторий
git clone https://github.com/sobue-code/rabbitmq_mcp.git
cd rabbitmq_mcp

# Установить зависимости
uv sync
```

Конфигурация для локальной установки:

```json
{
  "mcpServers": {
    "rabbitmq": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/rabbitmq_mcp",
        "rabbitmq-mcp-altqa"
      ],
      "env": {
        "RABBITMQ_HOST": "your-rabbitmq-host.com",
        "RABBITMQ_PORT": "5671",
        "RABBITMQ_USER": "your-username",
        "RABBITMQ_PASSWORD": "your-password",
        "RABBITMQ_VHOST": "your-vhost",
        "RABBITMQ_USE_SSL": "true",
        "RABBITMQ_CA_CERT": "/path/to/your/ca_cert.pem"
      }
    }
  }
}
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `RABBITMQ_HOST` | Хост RabbitMQ | `localhost` |
| `RABBITMQ_PORT` | Порт | `5672` |
| `RABBITMQ_USER` | Имя пользователя | `guest` |
| `RABBITMQ_PASSWORD` | Пароль | `guest` |
| `RABBITMQ_VHOST` | Виртуальный хост | `/` |
| `RABBITMQ_USE_SSL` | Использовать SSL (`true`/`false`) | `false` |
| `RABBITMQ_CA_CERT` | Путь к CA сертификату | (нет) |
| `RABBITMQ_HEARTBEAT` | Интервал heartbeat (сек) | `3600` |
| `RABBITMQ_SOCKET_TIMEOUT` | Таймаут сокета (сек) | `5` |

## Доступные инструменты

### Управление соединением

- `rabbitmq_connect` — Подключиться к RabbitMQ
- `rabbitmq_disconnect` — Отключиться
- `rabbitmq_status` — Проверить статус соединения

### Очереди

- `rabbitmq_declare_queue` — Создать очередь (quorum по умолчанию)
- `rabbitmq_delete_queue` — Удалить очередь
- `rabbitmq_purge_queue` — Очистить очередь
- `rabbitmq_queue_message_count` — Количество сообщений
- `rabbitmq_get_message` — Получить сообщение

### Exchanges

- `rabbitmq_declare_exchange` — Создать exchange
- `rabbitmq_delete_exchange` — Удалить exchange

### Связи

- `rabbitmq_bind_queue` — Привязать очередь к exchange
- `rabbitmq_unbind_queue` — Отвязать очередь

### Публикация

- `rabbitmq_publish` — Опубликовать в exchange
- `rabbitmq_publish_to_queue` — Опубликовать напрямую в очередь

## Примеры использования

### Подключение

```
Вызови rabbitmq_connect
```

### Проверка статуса

```
Проверь статус соединения через rabbitmq_status
```

### Создание очереди

```
Создай quorum очередь "my-queue" через rabbitmq_declare_queue
```

### Публикация сообщения

```
Опубликуй сообщение {"task": "test"} в exchange "" с routing key "my-queue"
```

### Получение сообщения

```
Получи сообщение из очереди "my-queue" через rabbitmq_get_message
```

## Разработка

```bash
# Клонировать и установить
git clone https://github.com/sobue-code/rabbitmq_mcp.git
cd rabbitmq_mcp
uv sync

# Тестирование сервера
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' | uv run rabbitmq-mcp-altqa
```

## Лицензия

Apache-2.0
