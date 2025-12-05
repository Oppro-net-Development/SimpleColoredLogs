![SimpleColoredLogs](img/SimpleColoredLogs.png)
# Professional Terminal Logger

Ein vollständiger, produktionsreifer Logger mit erweiterten Features für Python-Anwendungen und Discord Bots.

[](https://www.python.org/downloads/)
[](https://opensource.org/licenses/MIT)

## 🚀 Features

  - 🎨 **Farbige Terminal-Ausgabe** mit **162** vordefinierten Kategorien
  - 📁 **File-Logging** mit automatischer Rotation und Kompression
  - 🎯 **13 Log-Levels** von TRACE bis SECURITY mit Status-Tracking
  - 🧵 **Thread-safe** mit Lock-Mechanismus
  - 📊 **Multiple Output-Formate** (Simple, Standard, Detailed, JSON)
  - 🔒 **Sensitive Data Redaction** (Passwörter, API-Keys, Tokens)
  - 🌐 **Correlation IDs** für Request-Tracing über Microservices
  - 🏥 **Health Checks** & **Prometheus Metrics Export**
  - 🤖 **24 Discord-spezifische Kategorien** für Bot-Entwicklung

-----

## 📦 Installation

```bash
pip install SimpleColoredLogs
```

-----

## 🎯 Quick Start

### Basic Usage

```python
from logs import Logs, LogLevel, Category

# Konfiguration
Logs.configure(
    log_file="app.log",
    min_level=LogLevel.INFO,
    show_metadata=False
)

# Einfache Logs
Logs.trace(Category.SYSTEM, "Detailed debug info")
Logs.debug(Category.SYSTEM, "Debug information")
Logs.info(Category.SYSTEM, "Application started")
Logs.success(Category.DATABASE, "Connection established", host="localhost")
Logs.loading(Category.CONFIG, "Loading configuration files...")
Logs.processing(Category.WORKER, "Processing batch job", items=1000)
Logs.progress(Category.WORKER, 45, 100, "Processing files")
Logs.waiting(Category.API, "Waiting for API response...")
Logs.notice(Category.SYSTEM, "Configuration changed", key="timeout")
Logs.warn(Category.CACHE, "Hit rate low", rate=0.65)
Logs.error(Category.API, "Request failed", status=500)
Logs.critical(Category.DATABASE, "Connection pool exhausted")
Logs.fatal(Category.SYSTEM, "Application crash", reason="OutOfMemory")
Logs.security(Category.AUTH, "Unauthorized access attempt", ip="1.2.3.4")

# Exception Logging
try:
    raise ValueError("Something went wrong!")
except Exception as e:
    # Die Logs.exception Methode ist ein Alias für Logs.error mit traceback
    Logs.error(Category.SYSTEM, "Critical error", exception=e) 
```

### Discord Bot Usage

```python
from logs import Logs, Category

# Bot Startup
Logs.banner("🤖 Discord Bot Starting", Category.BOT)
Logs.loading(Category.INTENTS, "Configuring intents...")
Logs.success(Category.GATEWAY, "Connected to Discord", latency="42ms")

# Cog Loading
with Logs.context("CogLoader"):
    Logs.loading(Category.COGS, "Loading cogs...")
    Logs.success(Category.COGS, "Loaded cog", name="MusicCog", commands=12)
    Logs.warn(Category.COGS, "Warning", name="AdminCog", reason="Missing dependency")

# Command Execution
Logs.info(Category.SLASH_CMD, "Command invoked", command="/play", user="User#1234")
Logs.processing(Category.VOICE, "Joining voice channel...")
Logs.success(Category.VOICE, "Joined voice channel", channel="Music", members=5)

# Events
Logs.info(Category.EVENTS, "on_member_join", member="NewUser#5678")
Logs.info(Category.MESSAGE, "Message received", author="User#1234", channel="general")

# Moderation
Logs.warn(Category.MODERATION, "User kicked", user="BadUser#9999", reason="Spam")
Logs.security(Category.AUTOMOD, "AutoMod triggered", rule="No spam", action="timeout")

# Rate Limiting
Logs.warn(Category.RATELIMIT, "Rate limit hit", endpoint="/messages", retry_after=2.5)

# Sharding
Logs.info(Category.SHARDING, "Shard ready", shard_id=0, guilds=150, latency="42ms")
```

### Advanced Features

```python
# Performance Tracking
Logs.performance("database_query", Category.DATABASE)
# ... do work ...
duration = Logs.performance("database_query", Category.DATABASE) # Gibt Dauer zurück

# Context Manager
with Logs.context("UserRegistration"):
    Logs.loading(Category.USER, "Starting registration...")
    Logs.success(Category.AUTH, "User authenticated")
    Logs.info(Category.EMAIL, "Verification email sent")

# Event Logging
Logs.log_event("purchase_completed", Category.BUSINESS,
               order_id=12345, amount=99.99, currency="EUR")

# Distributed Tracing
Logs.set_correlation_id("req-abc-123-xyz")
Logs.info(Category.API, "Processing request", endpoint="/api/users")

# Tabellen (Achtung: Dies ist eine hypothetische Methode, falls du sie implementiert hast)
Logs.table(Category.METRICS,
           ["Service", "Status", "Response Time"],
           [["API", "UP", "45ms"],
            ["Database", "UP", "12ms"],
            ["Cache", "DOWN", "N/A"]])
```

-----

## 📊 Log Levels

| Level | Wert | Beschreibung |
| :--- | :--- | :--- |
| **TRACE** | -1 | Sehr detaillierte Debug-Infos |
| **DEBUG** | 0 | Standard Debug-Informationen |
| **INFO** | 1 | Allgemeine Informationen |
| **SUCCESS** | 2 | Erfolgreiche Operationen |
| **LOADING** | 3 | Lädt gerade etwas |
| **PROCESSING** | 4 | Verarbeitet Daten |
| **PROGRESS** | 5 | Fortschritts-Updates |
| **WAITING** | 6 | Wartet auf Ressourcen |
| **NOTICE** | 7 | Wichtige Hinweise |
| **WARN** | 8 | Warnungen |
| **ERROR** | 9 | Standard-Fehler |
| **CRITICAL** | 10 | Kritische Fehler |
| **FATAL** | 11 | Fatale Fehler (Absturz) |
| **SECURITY** | 12 | Sicherheitsvorfälle |

-----

## 🎨 Verfügbare Kategorien (148)

### Core System & Runtime

`API`, `DATABASE`, `SERVER`, `CACHE`, `AUTH`, `SYSTEM`, `CONFIG`, `SCHEMA`, `INDEX`, `QUERY`, `VIEW`, `TRANSACTION_COMMIT`, `NOSQL`,
`RELATIONAL_DB`, `SESSION_STORAGE`, **`RUNTIME`**, **`COMPILER`**, **`DEPENDENCY`**, **`CLI`**

### Network & Communication

`NETWORK`, `HTTP`, `WEBSOCKET`, `GRPC`, `GRAPHQL`, `REST`, `SOAP`, `LOAD_BALANCER`, `REVERSE_PROXY`, `DNS`, `CDN`, **`GEOLOCATION`**

### Security, Compliance & Fraud

`SECURITY`, `ENCRYPTION`, `FIREWALL`, `AUDIT`, `COMPLIANCE`, `VULNERABILITY`, `GDPR`, `HIPAA`, `PCI_DSS`, `IDP`, `MFA`, `RATE_LIMITER`, **`FRAUD`**

### Frontend, UI & Internationalisierung

`CLIENT`, `UI`, `UX`, `SPA`, `SSR`, `STATE`, `COMPONENT`, **`I18N`**

### Storage, Files & Assets

`FILE`, `STORAGE`, `BACKUP`, `SYNC`, `UPLOAD`, `DOWNLOAD`, **`ASSET`**

### Messaging & Events

`QUEUE`, `EVENT`, `PUBSUB`, `KAFKA`, `RABBITMQ`, `REDIS`

### External Services

`EMAIL`, `SMS`, `NOTIFICATION`, `PAYMENT`, `BILLING`, `STRIPE`, `PAYPAL`

### Monitoring & Observability

`METRICS`, `PERFORMANCE`, `HEALTH`, `MONITORING`, `TRACING`, `PROFILING`

### Data Processing & Transformation

`ETL`, `PIPELINE`, `WORKER`, `CRON`, `SCHEDULER`, `BATCH`, `STREAM`, **`MAPPING`**, **`TRANSFORM`**, **`REPORTING`**

### Business Logic, Finance & Inventory

`BUSINESS`, `WORKFLOW`, `TRANSACTION`, `ORDER`, `INVOICE`, `SHIPPING`, **`ACCOUNTING`**, **`INVENTORY`**

### User Management

`USER`, `SESSION`, `REGISTRATION`, `LOGIN`, `LOGOUT`, `PROFILE`

### AI & ML

`AI`, `ML`, `TRAINING`, `INFERENCE`, `MODEL`

### DevOps & Infrastructure

`DEPLOY`, `CI_CD`, `DOCKER`, `KUBERNETES`, `TERRAFORM`, `ANSIBLE`, `SERVERLESS`, `CONTAINER`, `IAC`, `VPC`, `AUTOSCALING`, **`PROVISION`**, **`DEPROVISION`**

### Testing & Quality

`TEST`, `UNITTEST`, `INTEGRATION`, `E2E`, `LOAD_TEST`

### Third Party Integrations

`SLACK`, `DISCORD`, `TWILIO`, `AWS`, `GCP`, `AZURE`

### Discord Bot Specific

`BOT`, `COGS`, `COMMANDS`, `EVENTS`, `VOICE`, `GUILD`, `MEMBER`, `CHANNEL`, `MESSAGE`, `REACTION`, `MODERATION`, `PERMISSIONS`, `EMBED`, `SLASH_CMD`, `BUTTON`, `MODAL`, `SELECT_MENU`, `AUTOMOD`, `WEBHOOK`, `PRESENCE`, `INTENTS`, `SHARDING`, `GATEWAY`, `RATELIMIT`

### Development

`DEBUG`, `DEV`, `STARTUP`, `SHUTDOWN`, `MIGRATION`, `UPDATE`, `VERSION`

-----

## 🔒 Security Features

### Sensitive Data Redaction

```python
# Aktivieren
Logs.enable_redaction()

# Automatisch erkannte Patterns:
# - Kreditkarten, SSN, Passwörter, API Keys, Tokens, Bearer Tokens

# Custom Pattern hinzufügen
Logs.add_redact_pattern(r'secret_code:\s*\S+')

# Deaktivieren
Logs.disable_redaction()
```

### Remote Log Forwarding

```python
# Zu Syslog/Logstash forwarden
Logs.enable_remote_forwarding("logserver.company.com", 514)
Logs.disable_remote_forwarding()
```

-----

## 📊 Monitoring & Health

### Health Checks

```python
# Health Status abrufen
health = Logs.health_check()
# {
#     "status": "healthy",
#     "total_logs": 1523,
#     "error_count": 12,
#     "error_rate": 0.008,
#     # ... weitere Metriken
# }

# Schöne Ausgabe
Logs.print_health()
```

### Statistiken

```python
# Statistiken abrufen
stats = Logs.stats(detailed=True)
Logs.print_stats()
```

### Prometheus Metrics

```python
# Metrics exportieren (im Prometheus-Textformat)
metrics = Logs.export_metrics_prometheus()
```

-----

## ⚙️ Konfiguration

```python
from logs import LogFormat, LogLevel

Logs.configure(
    enabled=True,
    show_timestamp=True,
    timestamp_format="%Y-%m-%d %H:%M:%S",
    min_level=LogLevel.DEBUG,
    log_file="app.log",
    colorize=True,
    format_type=LogFormat.STANDARD,  # SIMPLE, STANDARD, DETAILED, JSON
    show_metadata=False,
    max_file_size=10 * 1024 * 1024,  # 10MB
    backup_count=3,
    enable_redaction=True,
    enable_compression=True
)
```

### Rate Limiting

```python
# Max 500 Logs pro Minute
Logs.enable_rate_limiting(max_per_minute=500)
Logs.disable_rate_limiting()
```

### Sampling

```python
# Nur 10% der Logs ausgeben
Logs.set_sampling_rate(0.1)
```

### Adaptive Logging

```python
# Auto-Anpassung bei hoher Last (wechselt zu WARN bei >100 Logs/Minute)
Logs.enable_adaptive_logging(noise_threshold=100)
Logs.disable_adaptive_logging()
```

-----

## 🔍 Debug Tools

### Tail & Grep

```python
# Letzte 20 Logs anzeigen
last_logs = Logs.tail(20)

# Logs durchsuchen (Regex-Support)
errors = Logs.grep("error", case_sensitive=False, max_results=100)
api_errors = Logs.grep(r"API.*ERROR")
```

## 🎬 Session Recording

```python
# Session starten
Logs.start_session()
# ... Logs werden aufgezeichnet ...
logs = Logs.stop_session(save_to="session.json")
```

## 🔔 Alert System

```python
def email_alert(level, category, message):
    send_email(f"ALERT: {level} in {category}: {message}")

# Alert-Handler registrieren
Logs.add_alert(LogLevel.FATAL, email_alert)
Logs.set_alert_cooldown(300)  # 5 Minuten
```

-----

## 📝 Log-Formate

### SIMPLE

```
[INFO] [API] Request received
```

### STANDARD (Default)

```
[2024-01-15 14:30:45] [INFO] [API] Request received
```

### DETAILED

```
[2024-01-15 14:30:45] [INFO] [API] [main.py:123] Request received
```

### JSON

```json
{"timestamp": "2024-01-15T14:30:45", "level": "INFO", "category": "API", "message": "Request received"}
```

-----

## 🎯 Best Practices

### 1\. Strukturierte Logs mit Key-Value Pairs

```python
Logs.info(Category.API, "Request processed",
          method="POST",
          endpoint="/api/users",
          status=200,
          duration_ms=45.2)
```

### 2\. Context für zusammenhängende Operationen

```python
with Logs.context("OrderProcessing"):
    Logs.loading(Category.ORDER, "Processing order...")
    Logs.processing(Category.PAYMENT, "Processing payment...")
    Logs.success(Category.SHIPPING, "Shipment created")
```

### 3\. Performance Tracking

```python
# Verwenden Sie Logs.performance() für manuelle Messungen
# oder implementieren Sie einen Dekorator:
@Logs.measure(Category.DATABASE)
def expensive_database_query():
    # ... Datenbank-Code
    pass
```

### 4\. Correlation IDs für Microservices

```python
# Am Anfang jedes Requests
Logs.set_correlation_id(request.headers.get('X-Correlation-ID'))
Logs.info(Category.API, "Processing request")
```

-----

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome\! Feel free to open issues or submit pull requests.

-----

Made with ❤️ for Python developers and Discord bot creators