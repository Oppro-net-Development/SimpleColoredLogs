# 🎨 SimpleColoredLogs

Professional Terminal Logger für Python mit Farben, strukturiertem Logging und vielen Features.

## 📦 Installation

```bash
pip install SimpleColoredLogs
```

## 🚀 Schnellstart

```python
from logger import logger, Category

# Einfache Logs
logger.info(Category.API, "Server gestartet")
logger.success(Category.SYSTEM, "Konfiguration geladen")
logger.warn(Category.SECURITY, "Ungewöhnliche Aktivität")
logger.error(Category.DATABASE, "Verbindung fehlgeschlagen")
```

## 🎯 Features

- ✅ 15+ Log-Levels (TRACE, DEBUG, INFO, SUCCESS, WARN, ERROR, CRITICAL, FATAL, etc.)
- ✅ 50+ vordefinierte Kategorien (API, DATABASE, SECURITY, PAYMENT, etc.)
- ✅ Farbige Terminal-Ausgabe
- ✅ Strukturiertes Logging (JSON, Logfmt)
- ✅ Async-Mode für High-Performance
- ✅ Performance-Metriken
- ✅ Context-Management
- ✅ Exception-Handling mit Tracebacks
- ✅ Log-Rotation & Kompression
- ✅ Remote Logging (Syslog)
- ✅ Sensitive Data Redaction
- ✅ Distributed Tracing Support

## 📝 Verwendung

### Basis-Logging

```python
from logger import logger, Category, LogLevel

# Logger konfigurieren
logger.initialize(
    min_level=LogLevel.INFO,
    console=True,
    file_path="logs/app.log"
)

# Logs schreiben
logger.info(Category.API, "Request empfangen")
logger.success(Category.DATABASE, "Query erfolgreich")
logger.error(Category.SYSTEM, "Fehler aufgetreten")
```

### Mit Shortcuts

```python
from logger import logger, C

# Kürzer und übersichtlicher
logger.info(C.CORE.API, "API aufgerufen")
logger.error(C.SEC.FRAUD, "Betrugsversuch erkannt")
logger.success(C.BIZ.PAY, "Zahlung erfolgreich")
```

### Mit Context

```python
from logger import logger, Category

with logger.context("PaymentFlow"):
    logger.info(Category.PAYMENT, "Zahlung gestartet")
    logger.processing(Category.PAYMENT, "Verarbeite Transaktion")
    logger.success(Category.PAYMENT, "Zahlung abgeschlossen")
```

### Mit strukturierten Daten

```python
logger.info(
    Category.API,
    "Request verarbeitet",
    method="POST",
    endpoint="/api/users",
    status=201,
    duration_ms=45
)
```

### Exception Handling

```python
try:
    result = process_payment()
except Exception as e:
    logger.error(
        Category.PAYMENT,
        "Zahlung fehlgeschlagen",
        exception=e,  # Automatischer Traceback
        order_id=order_id
    )
```

### Performance-Messung

```python
# Mit Context Manager
with logger.measure(Category.DATABASE, "complex_query"):
    results = db.query("SELECT * FROM users")

# Als Decorator
@logger.timer(Category.API, "handle_request")
def handle_request():
    # ... code ...
    pass
```

## 🎨 Alle Log-Levels

```python
logger.trace(Category.DEBUG, "Sehr detailliert")
logger.debug(Category.DEBUG, "Debug-Info")
logger.info(Category.SYSTEM, "Information")
logger.success(Category.SYSTEM, "Erfolgreich")
logger.loading(Category.SYSTEM, "Lädt...")
logger.processing(Category.SYSTEM, "Verarbeitet...")
logger.progress(Category.SYSTEM, "Fortschritt", percent=75)
logger.waiting(Category.NETWORK, "Wartet...")
logger.notice(Category.SYSTEM, "Wichtiger Hinweis")
logger.warn(Category.SECURITY, "Warnung")
logger.error(Category.API, "Fehler")
logger.critical(Category.SYSTEM, "Kritisch")
logger.fatal(Category.SYSTEM, "Fatal")
logger.security(Category.SECURITY, "Sicherheits-Event")
```

## 📁 Kategorien

### Core System
`API`, `DATABASE`, `SERVER`, `CACHE`, `AUTH`, `SYSTEM`, `CONFIG`, `RUNTIME`

### Network
`NETWORK`, `HTTP`, `WEBSOCKET`, `GRPC`, `GRAPHQL`, `REST`, `DNS`, `CDN`

### Security
`SECURITY`, `ENCRYPTION`, `FIREWALL`, `AUDIT`, `FRAUD`, `MFA`

### Business
`BUSINESS`, `WORKFLOW`, `TRANSACTION`, `PAYMENT`, `ACCOUNTING`, `INVENTORY`

### Observability
`METRICS`, `PERFORMANCE`, `HEALTH`, `MONITORING`, `TRACING`

[Alle 50+ Kategorien in der Dokumentation](https://github.com/oppro-net/SimpleColoredLogs)

## 🔧 Konfiguration

### Via Code

```python
from logger import logger, LogLevel
from pathlib import Path

logger.initialize(
    min_level=LogLevel.DEBUG,
    console=True,
    console_colorized=True,
    file_path=Path("logs/app.log"),
    file_max_size=10 * 1024 * 1024,  # 10MB
    async_mode=True,
    sampling_rate=1.0
)
```

### Via Umgebungsvariablen

```bash
export LOG_LEVEL=DEBUG
export LOG_FILE=logs/app.log
export LOG_FORMAT=JSON
export LOG_COLORIZE=true
```

```python
# Lädt automatisch Umgebungsvariablen
logger.initialize(apply_env_vars=True)
```

## 🔌 Handler & Filter

### File Handler mit Rotation

```python
from logger import logger, FileHandler
from pathlib import Path

handler = FileHandler(
    filepath=Path("logs/app.log"),
    max_size=10 * 1024 * 1024,  # 10MB
    backup_count=5,
    compress=True
)
logger.add_handler(handler)
```

### Remote Logging

```python
from logger import logger, NetworkHandler

handler = NetworkHandler(
    host="logs.example.com",
    port=514,
    protocol="udp"
)
logger.add_handler(handler)
```

### Sensitive Data Redaction

```python
# Automatisches Entfernen von Passwörtern, API-Keys, etc.
logger.enable_redaction()

logger.info(Category.AUTH, "Login mit password=secret123")
# Output: "Login mit password=[REDACTED]"
```

## 📊 Spezielle Logger

### Audit Logger

```python
from logger import AuditLogger

audit = AuditLogger()

audit.log_access(
    user="john_doe",
    resource="/api/users",
    action="READ",
    result="SUCCESS"
)

audit.log_security_event(
    event="Failed login attempts",
    severity="HIGH",
    ip="192.168.1.100"
)
```

### Performance Logger

```python
from logger import PerformanceLogger

perf = PerformanceLogger()

perf.log_timing("api_response", 0.045)  # 45ms
perf.log_throughput("requests", count=1000, duration=60.0)
```

### Structured Logger

```python
from logger import StructuredLogger, Category

struct = StructuredLogger()

struct.log_event(
    event_type="order_placed",
    category=Category.BUSINESS,
    message="Bestellung aufgegeben",
    user_id=123,
    order_id=1001,
    amount=99.99
)
```

## 📈 Metriken

```python
# Metriken abrufen
metrics = logger.get_metrics()

print(f"Total Logs: {metrics['total_logs']}")
print(f"Errors: {metrics['error_count']}")
print(f"Avg Process Time: {metrics['avg_process_time_ms']} ms")

# Metriken zurücksetzen
logger.reset_metrics()
```

## 🌍 Distributed Tracing

```python
# Trace-IDs für Request-Tracking
logger.set_trace_id("req-12345")
logger.set_correlation_id("corr-67890")

logger.info(Category.API, "Request verarbeitet")
# Output enthält automatisch trace_id

logger.clear_tracing()
```

## 💡 Best Practices

### ✅ DO

```python
# Aussagekräftige Kategorien
logger.info(Category.API, "Request empfangen", endpoint="/users")

# Strukturierte Metadaten
logger.error(Category.DATABASE, "Query failed", 
            query=sql, error=str(e))

# Context für zusammenhängende Logs
with logger.context("OrderProcessing"):
    logger.info(Category.BUSINESS, "Verarbeite Bestellung")

# Exception-Parameter nutzen
logger.error(Category.SYSTEM, "Fehler", exception=e)
```

### ❌ DON'T

```python
# Zu generisch
logger.info("SYSTEM", "Irgendwas ist passiert")

# Fehlende Kontext-Infos
logger.error(Category.DATABASE, "Error")

# Exception als String (kein Traceback!)
logger.error(Category.SYSTEM, f"Error: {str(e)}")
```

## 📚 Beispiele

Siehe [`examples/`](examples/) Verzeichnis für:
- Basic Usage
- Async Logging
- Web App Integration
- Performance Monitoring
- Audit Trails

## 🛠️ Requirements

- Python 3.8+
- colorama (optional, für Windows)

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## 🤝 Contributing

Contributions sind willkommen! Siehe [CONTRIBUTING.md](CONTRIBUTING.md)

## 📧 Support

- 🐛 Bug Reports: [GitHub Issues](https://github.com/oppro-net/SimpleColoredLogs/issues)
- 💡 Feature Requests: [GitHub Discussions](https://github.com/oppro-net/SimpleColoredLogs/discussions)
- 📧 Email: contact@oppro.net

## ⭐ Support

Wenn dir SimpleColoredLogs gefällt, gib uns einen ⭐ auf [GitHub](https://github.com/oppro-net/SimpleColoredLogs)!

---

**Made with ❤️ by OPPRO.NET Network**
