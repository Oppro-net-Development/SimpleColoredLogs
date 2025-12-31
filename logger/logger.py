"""
Enhanced Professional Terminal Logger
Copyright (c) 2025 OPPRO.NET Network

Umfassend überarbeiteter Logger mit:
- Modularer Architektur
- Async Support
- Structured Logging
- Plugin-System
- Performance Optimierung
- Erweiterte Metriken
"""

import sys
import threading
import inspect
import traceback
import json
import os
import time
import atexit
import re
import socket
import gzip
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List, Union, ClassVar, TypeVar, Protocol
from pathlib import Path
from collections import defaultdict, deque
from enum import IntEnum, Enum
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from functools import wraps
import queue
import hashlib

try:
    from colorama import Fore, Style, Back, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    class MockColor:
        def __getattr__(self, name): return ""
    Fore = Style = Back = MockColor()
    COLORAMA_AVAILABLE = False


# ==========================================
# LOG LEVELS & TYPES
# ==========================================

class LogLevel(IntEnum):
    """Erweiterte Log-Level Definitionen"""
    TRACE = -1      
    DEBUG = 0       
    INFO = 1        
    SUCCESS = 2     
    LOADING = 3     
    PROCESSING = 4  
    PROGRESS = 5    
    WAITING = 6     
    NOTICE = 7      
    WARN = 8        
    ERROR = 9       
    CRITICAL = 10   
    FATAL = 11      
    SECURITY = 12   
    AUDIT = 13      # Neue Audit-Trail Logs
    METRIC = 14     # Performance Metriken


class LogFormat(IntEnum):
    """Output-Format Optionen"""
    SIMPLE = 0      
    STANDARD = 1    
    DETAILED = 2    
    JSON = 3        
    STRUCTURED = 4  # Neu: Strukturiertes Format
    LOGFMT = 5      # Neu: Logfmt-kompatibel


class OutputDestination(Enum):
    """Ausgabe-Ziele"""
    CONSOLE = "console"
    FILE = "file"
    SYSLOG = "syslog"
    NETWORK = "network"
    QUEUE = "queue"
    CUSTOM = "custom"


# ==========================================
# DATA STRUCTURES
# ==========================================

@dataclass
class LogEntry:
    """Strukturierte Log-Eintrag Datenklasse"""
    timestamp: datetime
    level: LogLevel
    category: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    context: List[str] = field(default_factory=list)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.name
        return data
    
    def to_json(self) -> str:
        """Konvertiert zu JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def to_logfmt(self) -> str:
        """Konvertiert zu Logfmt-Format"""
        parts = [
            f'ts={self.timestamp.isoformat()}',
            f'level={self.level.name}',
            f'category={self.category}',
            f'msg="{self.message}"'
        ]
        
        for k, v in self.metadata.items():
            parts.append(f'{k}={v}')
            
        if self.trace_id:
            parts.append(f'trace_id={self.trace_id}')
            
        return ' '.join(parts)


@dataclass
class LogMetrics:
    """Metriken für Log-Performance"""
    total_logs: int = 0
    logs_by_level: Dict[LogLevel, int] = field(default_factory=lambda: defaultdict(int))
    logs_by_category: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_count: int = 0
    warning_count: int = 0
    dropped_logs: int = 0
    average_process_time: float = 0.0
    peak_logs_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'total_logs': self.total_logs,
            'logs_by_level': {k.name: v for k, v in self.logs_by_level.items()},
            'logs_by_category': dict(self.logs_by_category),
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'dropped_logs': self.dropped_logs,
            'avg_process_time_ms': round(self.average_process_time * 1000, 2),
            'peak_logs_per_second': round(self.peak_logs_per_second, 2)
        }


# ==========================================
# CATEGORIES
# ==========================================

class Category(str, Enum):
    """Standard-Kategorien mit erweiterten Bereichen"""
    
    # Core System
    API = "API"
    DATABASE = "DATABASE"
    SERVER = "SERVER"
    CACHE = "CACHE"
    AUTH = "AUTH"
    SYSTEM = "SYSTEM"
    CONFIG = "CONFIG"
    RUNTIME = "RUNTIME"
    COMPILER = "COMPILER"
    DEPENDENCY = "DEPENDENCY"
    CLI = "CLI"
    
    # Network
    NETWORK = "NETWORK"
    HTTP = "HTTP"
    WEBSOCKET = "WEBSOCKET"
    GRPC = "GRPC"
    GRAPHQL = "GRAPHQL"
    REST = "REST"
    DNS = "DNS"
    CDN = "CDN"
    LOAD_BALANCER = "LOAD_BALANCER"
    GEOLOCATION = "GEOLOCATION"
    
    # Security
    SECURITY = "SECURITY"
    ENCRYPTION = "ENCRYPTION"
    FIREWALL = "FIREWALL"
    AUDIT = "AUDIT"
    COMPLIANCE = "COMPLIANCE"
    VULNERABILITY = "VULNERABILITY"
    FRAUD = "FRAUD"
    MFA = "MFA"
    RATE_LIMITER = "RATE_LIMITER"
    
    # Storage
    FILE = "FILE"
    STORAGE = "STORAGE"
    BACKUP = "BACKUP"
    SYNC = "SYNC"
    ASSET = "ASSET"
    
    # Messaging
    QUEUE = "QUEUE"
    EVENT = "EVENT"
    PUBSUB = "PUBSUB"
    KAFKA = "KAFKA"
    REDIS = "REDIS"
    
    # Business
    BUSINESS = "BUSINESS"
    WORKFLOW = "WORKFLOW"
    TRANSACTION = "TRANSACTION"
    PAYMENT = "PAYMENT"
    ACCOUNTING = "ACCOUNTING"
    INVENTORY = "INVENTORY"
    
    # Observability
    METRICS = "METRICS"
    PERFORMANCE = "PERFORMANCE"
    HEALTH = "HEALTH"
    MONITORING = "MONITORING"
    TRACING = "TRACING"
    
    # DevOps
    DEPLOY = "DEPLOY"
    CI_CD = "CI/CD"
    DOCKER = "DOCKER"
    KUBERNETES = "K8S"
    TERRAFORM = "TERRAFORM"
    
    # AI/ML
    AI = "AI"
    ML = "ML"
    TRAINING = "TRAINING"
    INFERENCE = "INFERENCE"
    
    # Testing
    TEST = "TEST"
    UNITTEST = "UNITTEST"
    INTEGRATION = "INTEGRATION"
    E2E = "E2E"
    
    # Development
    DEBUG = "DEBUG"
    DEV = "DEV"
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"


class CategoryColors:
    """Verbesserte Farb-Mappings"""
    
    COLORS: ClassVar[Dict[Category, str]] = {
        # Core - Blau/Cyan Töne
        Category.API: Fore.BLUE + Style.BRIGHT,
        Category.DATABASE: Fore.MAGENTA + Style.BRIGHT,
        Category.SERVER: Fore.CYAN + Style.BRIGHT,
        Category.CACHE: Fore.YELLOW,
        Category.AUTH: Fore.RED + Style.BRIGHT,
        Category.SYSTEM: Fore.WHITE + Style.BRIGHT,
        Category.CONFIG: Fore.LIGHTMAGENTA_EX,
        Category.RUNTIME: Fore.YELLOW + Style.BRIGHT,
        Category.COMPILER: Fore.LIGHTBLUE_EX + Style.BRIGHT,
        Category.DEPENDENCY: Fore.LIGHTCYAN_EX,
        Category.CLI: Fore.WHITE + Style.BRIGHT,
        
        # Network - Cyan/Blau Varianten
        Category.NETWORK: Fore.LIGHTBLUE_EX,
        Category.HTTP: Fore.BLUE,
        Category.WEBSOCKET: Fore.LIGHTBLUE_EX + Style.BRIGHT,
        Category.GRPC: Fore.CYAN + Style.BRIGHT,
        Category.GRAPHQL: Fore.MAGENTA,
        Category.REST: Fore.BLUE,
        Category.DNS: Fore.LIGHTGREEN_EX,
        Category.CDN: Fore.MAGENTA + Style.BRIGHT,
        Category.LOAD_BALANCER: Fore.YELLOW + Style.BRIGHT,
        Category.GEOLOCATION: Fore.LIGHTYELLOW_EX,
        
        # Security - Rot/Orange Töne
        Category.SECURITY: Fore.LIGHTRED_EX + Style.BRIGHT,
        Category.ENCRYPTION: Fore.RED + Style.BRIGHT,
        Category.FIREWALL: Fore.RED,
        Category.AUDIT: Fore.LIGHTRED_EX,
        Category.COMPLIANCE: Fore.MAGENTA,
        Category.VULNERABILITY: Fore.RED + Back.WHITE,
        Category.FRAUD: Fore.RED + Back.YELLOW,
        Category.MFA: Fore.LIGHTCYAN_EX,
        Category.RATE_LIMITER: Fore.YELLOW + Style.BRIGHT,
        
        # Storage - Grün Töne
        Category.FILE: Fore.LIGHTGREEN_EX,
        Category.STORAGE: Fore.GREEN,
        Category.BACKUP: Fore.GREEN + Style.BRIGHT,
        Category.SYNC: Fore.CYAN,
        Category.ASSET: Fore.MAGENTA,
        
        # Business - Gelb/Grün
        Category.BUSINESS: Fore.WHITE + Style.BRIGHT,
        Category.WORKFLOW: Fore.CYAN,
        Category.TRANSACTION: Fore.GREEN + Style.BRIGHT,
        Category.PAYMENT: Fore.GREEN + Style.BRIGHT,
        Category.ACCOUNTING: Fore.GREEN + Back.BLACK,
        Category.INVENTORY: Fore.LIGHTMAGENTA_EX,
        
        # Observability - Gelb Töne
        Category.METRICS: Fore.LIGHTYELLOW_EX,
        Category.PERFORMANCE: Fore.YELLOW + Style.BRIGHT,
        Category.HEALTH: Fore.GREEN,
        Category.MONITORING: Fore.CYAN,
        Category.TRACING: Fore.LIGHTCYAN_EX,
        
        # Development - Grau/Weiß Töne
        Category.DEBUG: Fore.LIGHTBLACK_EX,
        Category.DEV: Fore.CYAN,
        Category.STARTUP: Fore.GREEN + Style.BRIGHT,
        Category.SHUTDOWN: Fore.RED + Style.BRIGHT,
    }
    
    @classmethod
    def get_color(cls, category: Union[Category, str]) -> str:
        """Gibt die Farbe für eine Kategorie zurück"""
        if isinstance(category, str):
            try:
                category = Category(category)
            except ValueError:
                return Style.BRIGHT
        return cls.COLORS.get(category, Style.BRIGHT)


class LevelColors:
    """Farb-Mappings für Log-Levels"""
    
    COLORS: ClassVar[Dict[LogLevel, str]] = {
        LogLevel.TRACE: Fore.LIGHTBLACK_EX,
        LogLevel.DEBUG: Fore.CYAN,
        LogLevel.INFO: Fore.WHITE,
        LogLevel.SUCCESS: Fore.GREEN + Style.BRIGHT,
        LogLevel.LOADING: Fore.BLUE,
        LogLevel.PROCESSING: Fore.LIGHTCYAN_EX,
        LogLevel.PROGRESS: Fore.LIGHTBLUE_EX,
        LogLevel.WAITING: Fore.LIGHTYELLOW_EX,
        LogLevel.NOTICE: Fore.LIGHTMAGENTA_EX,
        LogLevel.WARN: Fore.YELLOW + Style.BRIGHT,
        LogLevel.ERROR: Fore.RED + Style.BRIGHT,
        LogLevel.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
        LogLevel.FATAL: Fore.WHITE + Back.RED + Style.BRIGHT,
        LogLevel.SECURITY: Fore.BLACK + Back.YELLOW + Style.BRIGHT,
        LogLevel.AUDIT: Fore.LIGHTMAGENTA_EX + Style.BRIGHT,
        LogLevel.METRIC: Fore.LIGHTYELLOW_EX,
    }
    
    @classmethod
    def get_color(cls, level: LogLevel) -> str:
        """Gibt die Farbe für ein Log-Level zurück"""
        return cls.COLORS.get(level, Fore.WHITE)


# ==========================================
# PLUGINS & HANDLERS
# ==========================================

class LogHandler(Protocol):
    """Protocol für Log-Handler"""
    def handle(self, entry: LogEntry) -> None: ...


class LogFilter(Protocol):
    """Protocol für Log-Filter"""
    def filter(self, entry: LogEntry) -> bool: ...


class ConsoleHandler:
    """Handler für Konsolen-Ausgabe"""
    
    def __init__(self, colorize: bool = True, stream=None):
        self.colorize = colorize and COLORAMA_AVAILABLE
        self.stream = stream or sys.stdout
        
    def handle(self, entry: LogEntry) -> None:
        """Gibt Log-Eintrag auf der Konsole aus"""
        formatted = self._format_entry(entry)
        
        # Fehler/Warnungen auf stderr
        stream = sys.stderr if entry.level >= LogLevel.WARN else self.stream
        print(formatted, file=stream)
    
    def _format_entry(self, entry: LogEntry) -> str:
        """Formatiert Log-Eintrag für die Konsole"""
        if not self.colorize:
            return self._format_plain(entry)
        
        level_color = LevelColors.get_color(entry.level)
        category_color = CategoryColors.get_color(entry.category)
        msg_color = Fore.RED if entry.level >= LogLevel.ERROR else Fore.WHITE
        
        timestamp = f"{Style.DIM}[{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]{Style.RESET_ALL}"
        level = f"{level_color}{Style.BRIGHT}[{entry.level.name:<10}]{Style.RESET_ALL}"
        category = f"{category_color}[{entry.category}]{Style.RESET_ALL}"
        message = f"{msg_color}{entry.message}{Style.RESET_ALL}"
        
        parts = [timestamp, level, category]
        
        # Context
        if entry.context:
            ctx = " > ".join(entry.context)
            parts.append(f"{Style.DIM}({ctx}){Style.RESET_ALL}")
        
        # Trace IDs
        if entry.trace_id:
            parts.append(f"{Style.DIM}[trace:{entry.trace_id[:8]}]{Style.RESET_ALL}")
        
        parts.append(message)
        
        return " ".join(parts)
    
    def _format_plain(self, entry: LogEntry) -> str:
        """Formatiert ohne Farben"""
        timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        parts = [f"[{timestamp}]", f"[{entry.level.name}]", f"[{entry.category}]"]
        
        if entry.context:
            parts.append(f"({' > '.join(entry.context)})")
        
        parts.append(entry.message)
        return " ".join(parts)


class FileHandler:
    """Handler für Datei-Ausgabe mit Rotation"""
    
    def __init__(self, 
                 filepath: Path,
                 max_size: int = 10 * 1024 * 1024,
                 backup_count: int = 5,
                 compress: bool = True):
        self.filepath = Path(filepath)
        self.max_size = max_size
        self.backup_count = backup_count
        self.compress = compress
        self._lock = threading.Lock()
        
        # Erstelle Verzeichnis
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def handle(self, entry: LogEntry) -> None:
        """Schreibt Log-Eintrag in Datei"""
        with self._lock:
            # Rotation prüfen
            if self.filepath.exists() and self.filepath.stat().st_size > self.max_size:
                self._rotate()
            
            # Schreiben
            line = self._format_entry(entry) + "\n"
            self.filepath.open('a', encoding='utf-8').write(line)
    
    def _format_entry(self, entry: LogEntry) -> str:
        """Formatiert Log-Eintrag für Datei (ohne Farben)"""
        timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return f"[{timestamp}] [{entry.level.name}] [{entry.category}] {entry.message}"
    
    def _rotate(self):
        """Rotiert Log-Dateien"""
        # Älteste löschen
        oldest = self.filepath.with_suffix(f"{self.filepath.suffix}.{self.backup_count}")
        if oldest.exists():
            oldest.unlink()
        
        # Verschieben
        for i in range(self.backup_count - 1, 0, -1):
            src = self.filepath.with_suffix(f"{self.filepath.suffix}.{i}")
            dst = self.filepath.with_suffix(f"{self.filepath.suffix}.{i + 1}")
            if src.exists():
                if self.compress and i == self.backup_count - 1:
                    self._compress_file(src, dst.with_suffix('.gz'))
                    src.unlink()
                else:
                    src.rename(dst)
        
        # Aktuelle Datei
        if self.filepath.exists():
            self.filepath.rename(self.filepath.with_suffix(f"{self.filepath.suffix}.1"))
    
    def _compress_file(self, src: Path, dst: Path):
        """Komprimiert eine Datei"""
        with open(src, 'rb') as f_in:
            with gzip.open(dst, 'wb') as f_out:
                f_out.writelines(f_in)


class NetworkHandler:
    """Handler für Remote-Logging (Syslog-Style)"""
    
    def __init__(self, host: str, port: int = 514, protocol: str = 'udp'):
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self._socket = None
        self._lock = threading.Lock()
    
    def handle(self, entry: LogEntry) -> None:
        """Sendet Log-Eintrag an Remote-Server"""
        try:
            message = entry.to_json().encode('utf-8')
            
            with self._lock:
                if not self._socket:
                    self._connect()
                
                if self.protocol == 'udp':
                    self._socket.sendto(message, (self.host, self.port))
                else:
                    self._socket.send(message + b'\n')
        except Exception:
            pass  # Silent fail für Network-Handler
    
    def _connect(self):
        """Erstellt Socket-Verbindung"""
        if self.protocol == 'udp':
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.host, self.port))
        self._socket.settimeout(1)


class LevelFilter:
    """Filtert nach Minimum Log-Level"""
    
    def __init__(self, min_level: LogLevel):
        self.min_level = min_level
    
    def filter(self, entry: LogEntry) -> bool:
        return entry.level >= self.min_level


class CategoryFilter:
    """Filtert nach Kategorien"""
    
    def __init__(self, 
                 include: Optional[List[str]] = None,
                 exclude: Optional[List[str]] = None):
        self.include = set(include) if include else None
        self.exclude = set(exclude) if exclude else set()
    
    def filter(self, entry: LogEntry) -> bool:
        if entry.category in self.exclude:
            return False
        if self.include and entry.category not in self.include:
            return False
        return True


class SamplingFilter:
    """Sample-basiertes Filtering"""
    
    def __init__(self, rate: float = 1.0):
        self.rate = max(0.0, min(1.0, rate))
    
    def filter(self, entry: LogEntry) -> bool:
        if self.rate >= 1.0:
            return True
        return random.random() < self.rate


# ==========================================
# MAIN LOGGER CLASS
# ==========================================

class EnhancedLogger:
    """
    Erweiterter Professional Logger mit Plugin-System
    """
    
    # Konfiguration
    enabled: bool = True
    min_level: LogLevel = LogLevel.DEBUG
    format_type: LogFormat = LogFormat.STANDARD
    
    # Handler & Filter
    _handlers: List[LogHandler] = []
    _filters: List[LogFilter] = []
    
    # State Management
    _lock = threading.Lock()
    _context_stack: List[str] = []
    _metrics = LogMetrics()
    _trace_id: Optional[str] = None
    _correlation_id: Optional[str] = None
    
    # Async Support
    _async_queue: Optional[queue.Queue] = None
    _async_worker: Optional[threading.Thread] = None
    _shutdown_event = threading.Event()
    
    # Performance Tracking
    _process_times: deque = deque(maxlen=1000)
    _log_timestamps: deque = deque(maxlen=100)
    
    # Sensitive Data Redaction
    _redact_enabled: bool = False
    _redact_patterns: List[re.Pattern] = []
    
    @classmethod
    def initialize(cls,
                   min_level: LogLevel = LogLevel.DEBUG,
                   console: bool = True,
                   console_colorized: bool = True,
                   file_path: Optional[Path] = None,
                   file_max_size: int = 10 * 1024 * 1024,
                   async_mode: bool = False,
                   sampling_rate: float = 1.0):
        """Initialisiert den Logger mit Basis-Konfiguration"""
        
        with cls._lock:
            cls.min_level = min_level
            cls._handlers = []
            cls._filters = []
            
            # Standard-Filter
            cls._filters.append(LevelFilter(min_level))
            
            if sampling_rate < 1.0:
                cls._filters.append(SamplingFilter(sampling_rate))
            
            # Standard-Handler
            if console:
                cls._handlers.append(ConsoleHandler(colorize=console_colorized))
            
            if file_path:
                cls._handlers.append(FileHandler(
                    filepath=file_path,
                    max_size=file_max_size
                ))
            
            # Async Mode
            if async_mode:
                cls._enable_async_mode()
            
            # Umgebungsvariablen laden
            cls._load_env_config()
    
    @classmethod
    def _enable_async_mode(cls):
        """Aktiviert asynchronen Logging-Modus"""
        cls._async_queue = queue.Queue(maxsize=10000)
        cls._shutdown_event.clear()
        
        def worker():
            while not cls._shutdown_event.is_set():
                try:
                    entry = cls._async_queue.get(timeout=0.1)
                    cls._process_entry_sync(entry)
                    cls._async_queue.task_done()
                except queue.Empty:
                    continue
        
        cls._async_worker = threading.Thread(target=worker, daemon=True)
        cls._async_worker.start()
    
    @classmethod
    def _load_env_config(cls):
        """Lädt Konfiguration aus Umgebungsvariablen"""
        # LOG_LEVEL
        level_str = os.getenv('LOG_LEVEL', '').upper()
        if level_str:
            try:
                cls.min_level = LogLevel[level_str]
            except KeyError:
                pass
        
        # LOG_FILE
        file_path = os.getenv('LOG_FILE')
        if file_path:
            cls.add_handler(FileHandler(Path(file_path)))
        
        # LOG_FORMAT
        format_str = os.getenv('LOG_FORMAT', '').upper()
        if format_str:
            try:
                cls.format_type = LogFormat[format_str]
            except KeyError:
                pass
        
        # LOG_SAMPLING_RATE
        sampling = os.getenv('LOG_SAMPLING_RATE')
        if sampling:
            try:
                rate = float(sampling)
                cls.add_filter(SamplingFilter(rate))
            except ValueError:
                pass
    
    @classmethod
    def add_handler(cls, handler: LogHandler):
        """Fügt einen Handler hinzu"""
        with cls._lock:
            cls._handlers.append(handler)
    
    @classmethod
    def add_filter(cls, filter: LogFilter):
        """Fügt einen Filter hinzu"""
        with cls._lock:
            cls._filters.append(filter)
    
    @classmethod
    def remove_handler(cls, handler: LogHandler):
        """Entfernt einen Handler"""
        with cls._lock:
            if handler in cls._handlers:
                cls._handlers.remove(handler)
    
    @classmethod
    def enable_redaction(cls, patterns: Optional[List[str]] = None):
        """Aktiviert Sensitive-Data Redaction"""
        cls._redact_enabled = True
        
        default_patterns = [
            r'\b\d{13,19}\b',  # Kreditkarten
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'password["\s:=]+\S+',
            r'api[_-]?key["\s:=]+\S+',
            r'secret["\s:=]+\S+',
            r'token["\s:=]+\S+',
            r'Bearer\s+\S+',
        ]
        
        patterns = patterns or default_patterns
        cls._redact_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    @classmethod
    def _redact_message(cls, message: str) -> str:
        """Entfernt sensible Daten"""
        if not cls._redact_enabled:
            return message
        
        for pattern in cls._redact_patterns:
            message = pattern.sub('[REDACTED]', message)
        return message
    
    @classmethod
    def _get_caller_info(cls) -> Dict[str, Any]:
        """Holt Informationen über den Aufrufer"""
        try:
            frame = inspect.stack()[4]  # 0=stack, 1=_get_caller, 2=_log, 3=public, 4=caller
            return {
                "file": Path(frame.filename).name,
                "line": frame.lineno,
                "function": frame.function,
                "thread": threading.current_thread().name
            }
        except:
            return {"file": "", "line": 0, "function": "", "thread": ""}
    
    @classmethod
    def _create_entry(cls,
                      level: LogLevel,
                      category: Union[Category, str],
                      message: str,
                      extra: Optional[Dict] = None) -> LogEntry:
        """Erstellt einen Log-Eintrag"""
        
        # Kategorie normalisieren
        if isinstance(category, Category):
            category_str = category.value
        else:
            category_str = str(category)
        
        # Message redactieren
        message = cls._redact_message(message)
        
        # Metadata sammeln
        metadata = cls._get_caller_info()
        
        # Entry erstellen
        return LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category_str,
            message=message,
            metadata=metadata,
            extra=extra or {},
            context=list(cls._context_stack),
            trace_id=cls._trace_id,
            correlation_id=cls._correlation_id
        )
    
    @classmethod
    def _should_log(cls, entry: LogEntry) -> bool:
        """Prüft ob Log-Eintrag verarbeitet werden soll"""
        if not cls.enabled:
            return False
        
        for filter in cls._filters:
            if not filter.filter(entry):
                return False
        
        return True
    
    @classmethod
    def _process_entry(cls, entry: LogEntry):
        """Verarbeitet einen Log-Eintrag"""
        start_time = time.perf_counter()
        
        if cls._async_queue:
            # Async Mode
            try:
                cls._async_queue.put_nowait(entry)
            except queue.Full:
                cls._metrics.dropped_logs += 1
        else:
            # Sync Mode
            cls._process_entry_sync(entry)
        
        # Performance Tracking
        process_time = time.perf_counter() - start_time
        cls._process_times.append(process_time)
        
        # Metriken aktualisieren
        cls._update_metrics(entry, process_time)
    
    @classmethod
    def _process_entry_sync(cls, entry: LogEntry):
        """Verarbeitet einen Log-Eintrag synchron"""
        for handler in cls._handlers:
            try:
                handler.handle(entry)
            except Exception as e:
                # Handler-Fehler nicht nach oben propagieren
                print(f"Handler error: {e}", file=sys.stderr)
    
    @classmethod
    def _update_metrics(cls, entry: LogEntry, process_time: float):
        """Aktualisiert interne Metriken"""
        cls._metrics.total_logs += 1
        cls._metrics.logs_by_level[entry.level] += 1
        cls._metrics.logs_by_category[entry.category] += 1
        
        if entry.level >= LogLevel.ERROR:
            cls._metrics.error_count += 1
        elif entry.level == LogLevel.WARN:
            cls._metrics.warning_count += 1
        
        # Durchschnittliche Verarbeitungszeit
        if cls._process_times:
            cls._metrics.average_process_time = sum(cls._process_times) / len(cls._process_times)
        
        # Peak Logs pro Sekunde
        now = time.time()
        cls._log_timestamps.append(now)
        
        if len(cls._log_timestamps) > 1:
            time_span = cls._log_timestamps[-1] - cls._log_timestamps[0]
            if time_span > 0:
                current_rate = len(cls._log_timestamps) / time_span
                cls._metrics.peak_logs_per_second = max(
                    cls._metrics.peak_logs_per_second,
                    current_rate
                )
    
    @classmethod
    def _log(cls,
             level: LogLevel,
             category: Union[Category, str],
             message: str,
             exception: Optional[BaseException] = None,
             **kwargs):
        """Zentrale Log-Methode"""
        
        # Exception-Handling
        if exception:
            trace = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
            message = f"{message}\n{trace}"
        
        # Entry erstellen
        entry = cls._create_entry(level, category, message, extra=kwargs)
        
        # Filtern und verarbeiten
        if cls._should_log(entry):
            cls._process_entry(entry)
    
    # ==========================================
    # PUBLIC LOGGING METHODS
    # ==========================================
    
    @classmethod
    def trace(cls, category: Union[Category, str], message: str, **kwargs):
        """Trace-Level Log"""
        cls._log(LogLevel.TRACE, category, message, **kwargs)
    
    @classmethod
    def debug(cls, category: Union[Category, str], message: str, **kwargs):
        """Debug-Level Log"""
        cls._log(LogLevel.DEBUG, category, message, **kwargs)
    
    @classmethod
    def info(cls, category: Union[Category, str], message: str, **kwargs):
        """Info-Level Log"""
        cls._log(LogLevel.INFO, category, message, **kwargs)
    
    @classmethod
    def success(cls, category: Union[Category, str], message: str, **kwargs):
        """Success-Level Log"""
        cls._log(LogLevel.SUCCESS, category, message, **kwargs)
    
    @classmethod
    def loading(cls, category: Union[Category, str], message: str, **kwargs):
        """Loading-Level Log"""
        cls._log(LogLevel.LOADING, category, message, **kwargs)
    
    @classmethod
    def processing(cls, category: Union[Category, str], message: str, **kwargs):
        """Processing-Level Log"""
        cls._log(LogLevel.PROCESSING, category, message, **kwargs)
    
    @classmethod
    def progress(cls, category: Union[Category, str], message: str, percent: Optional[float] = None, **kwargs):
        """Progress-Level Log mit optionalem Prozentsatz"""
        if percent is not None:
            message = f"{message} ({percent:.1f}%)"
        cls._log(LogLevel.PROGRESS, category, message, **kwargs)
    
    @classmethod
    def waiting(cls, category: Union[Category, str], message: str, **kwargs):
        """Waiting-Level Log"""
        cls._log(LogLevel.WAITING, category, message, **kwargs)
    
    @classmethod
    def notice(cls, category: Union[Category, str], message: str, **kwargs):
        """Notice-Level Log"""
        cls._log(LogLevel.NOTICE, category, message, **kwargs)
    
    @classmethod
    def warn(cls, category: Union[Category, str], message: str, **kwargs):
        """Warning-Level Log"""
        cls._log(LogLevel.WARN, category, message, **kwargs)
    
    @classmethod
    def error(cls, category: Union[Category, str], message: str, 
              exception: Optional[BaseException] = None, **kwargs):
        """Error-Level Log"""
        cls._log(LogLevel.ERROR, category, message, exception=exception, **kwargs)
    
    @classmethod
    def critical(cls, category: Union[Category, str], message: str,
                 exception: Optional[BaseException] = None, **kwargs):
        """Critical-Level Log"""
        cls._log(LogLevel.CRITICAL, category, message, exception=exception, **kwargs)
    
    @classmethod
    def fatal(cls, category: Union[Category, str], message: str,
              exception: Optional[BaseException] = None, **kwargs):
        """Fatal-Level Log"""
        cls._log(LogLevel.FATAL, category, message, exception=exception, **kwargs)
    
    @classmethod
    def security(cls, category: Union[Category, str], message: str, **kwargs):
        """Security-Level Log"""
        cls._log(LogLevel.SECURITY, category, message, **kwargs)
    
    @classmethod
    def audit(cls, category: Union[Category, str], message: str, **kwargs):
        """Audit-Level Log"""
        cls._log(LogLevel.AUDIT, category, message, **kwargs)
    
    @classmethod
    def metric(cls, category: Union[Category, str], message: str, **kwargs):
        """Metric-Level Log"""
        cls._log(LogLevel.METRIC, category, message, **kwargs)
    
    # ==========================================
    # CONTEXT MANAGEMENT
    # ==========================================
    
    @classmethod
    def push_context(cls, context: str):
        """Fügt einen Kontext zum Stack hinzu"""
        with cls._lock:
            cls._context_stack.append(context)
    
    @classmethod
    def pop_context(cls) -> Optional[str]:
        """Entfernt den obersten Kontext vom Stack"""
        with cls._lock:
            if cls._context_stack:
                return cls._context_stack.pop()
            return None
    
    @classmethod
    @contextmanager
    def context(cls, context: str):
        """Context Manager für temporären Kontext"""
        cls.push_context(context)
        try:
            yield
        finally:
            cls.pop_context()
    
    @classmethod
    def set_trace_id(cls, trace_id: str):
        """Setzt eine Trace-ID für Distributed Tracing"""
        cls._trace_id = trace_id
    
    @classmethod
    def set_correlation_id(cls, correlation_id: str):
        """Setzt eine Correlation-ID für Request-Tracking"""
        cls._correlation_id = correlation_id
    
    @classmethod
    def clear_tracing(cls):
        """Löscht alle Tracing-IDs"""
        cls._trace_id = None
        cls._correlation_id = None
    
    # ==========================================
    # PERFORMANCE & METRICS
    # ==========================================
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Gibt aktuelle Metriken zurück"""
        return cls._metrics.to_dict()
    
    @classmethod
    def reset_metrics(cls):
        """Setzt Metriken zurück"""
        with cls._lock:
            cls._metrics = LogMetrics()
            cls._process_times.clear()
            cls._log_timestamps.clear()
    
    @classmethod
    @contextmanager
    def measure(cls, category: Union[Category, str], operation: str):
        """Context Manager für Performance-Messung"""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            cls.metric(category, f"{operation} completed", duration_ms=round(duration * 1000, 2))
    
    @classmethod
    def timer(cls, category: Union[Category, str], operation: str):
        """Decorator für Performance-Messung"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with cls.measure(category, operation or func.__name__):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    # ==========================================
    # ASYNC SUPPORT
    # ==========================================
    
    @classmethod
    async def async_log(cls, 
                       level: LogLevel,
                       category: Union[Category, str],
                       message: str,
                       **kwargs):
        """Asynchrone Log-Methode"""
        await asyncio.get_event_loop().run_in_executor(
            None, cls._log, level, category, message, None, **kwargs
        )
    
    @classmethod
    async def async_info(cls, category: Union[Category, str], message: str, **kwargs):
        """Async Info Log"""
        await cls.async_log(LogLevel.INFO, category, message, **kwargs)
    
    @classmethod
    async def async_error(cls, category: Union[Category, str], message: str, 
                         exception: Optional[BaseException] = None, **kwargs):
        """Async Error Log"""
        if exception:
            trace = ''.join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
            message = f"{message}\n{trace}"
        await cls.async_log(LogLevel.ERROR, category, message, **kwargs)
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    @classmethod
    def flush(cls):
        """Flushed alle gepufferten Logs"""
        if cls._async_queue:
            cls._async_queue.join()
    
    @classmethod
    def shutdown(cls):
        """Fährt den Logger sauber herunter"""
        cls.flush()
        
        if cls._async_worker:
            cls._shutdown_event.set()
            cls._async_worker.join(timeout=5)
        
        cls._handlers.clear()
        cls._filters.clear()
    
    @classmethod
    def get_log_levels(cls) -> List[str]:
        """Gibt alle verfügbaren Log-Levels zurück"""
        return [level.name for level in LogLevel]
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Gibt alle Standard-Kategorien zurück"""
        return [cat.value for cat in Category]


# ==========================================
# CONVENIENCE ALIASES & SHORTCUTS
# ==========================================

# Globaler Logger-Alias
logger = EnhancedLogger

# Kategorie-Shortcuts
class L:
    """Log-Level Shortcuts"""
    TRACE = LogLevel.TRACE
    DEBUG = LogLevel.DEBUG
    INFO = LogLevel.INFO
    SUCCESS = LogLevel.SUCCESS
    WARN = LogLevel.WARN
    ERROR = LogLevel.ERROR
    CRITICAL = LogLevel.CRITICAL
    FATAL = LogLevel.FATAL


class C:
    """Category Shortcuts - Hierarchisch organisiert"""
    
    class CORE:
        API = Category.API
        DB = Category.DATABASE
        SERVER = Category.SERVER
        CACHE = Category.CACHE
        AUTH = Category.AUTH
        SYS = Category.SYSTEM
        CFG = Category.CONFIG
        RUNTIME = Category.RUNTIME
    
    class NET:
        BASE = Category.NETWORK
        HTTP = Category.HTTP
        WS = Category.WEBSOCKET
        GRPC = Category.GRPC
        GQL = Category.GRAPHQL
        REST = Category.REST
        DNS = Category.DNS
    
    class SEC:
        BASE = Category.SECURITY
        ENCRYPT = Category.ENCRYPTION
        FW = Category.FIREWALL
        AUDIT = Category.AUDIT
        FRAUD = Category.FRAUD
        MFA = Category.MFA
    
    class STORE:
        FILE = Category.FILE
        BASE = Category.STORAGE
        BACKUP = Category.BACKUP
        SYNC = Category.SYNC
    
    class BIZ:
        BASE = Category.BUSINESS
        WORKFLOW = Category.WORKFLOW
        TX = Category.TRANSACTION
        PAY = Category.PAYMENT
        ACCT = Category.ACCOUNTING
    
    class OBS:
        METRICS = Category.METRICS
        PERF = Category.PERFORMANCE
        HEALTH = Category.HEALTH
        TRACE = Category.TRACING
    
    class DEV:
        DEBUG = Category.DEBUG
        TEST = Category.TEST
        START = Category.STARTUP
        STOP = Category.SHUTDOWN


# ==========================================
# SPECIALIZED LOGGERS
# ==========================================

class StructuredLogger(EnhancedLogger):
    """Logger mit erzwungenem strukturiertem Format"""
    
    @classmethod
    def initialize(cls, **kwargs):
        """Überschreibt Standard-Format"""
        kwargs['format_type'] = LogFormat.STRUCTURED
        super().initialize(**kwargs)
    
    @classmethod
    def log_event(cls, 
                  event_type: str,
                  category: Union[Category, str],
                  message: str,
                  **data):
        """Logged ein strukturiertes Event"""
        cls.info(category, message, event_type=event_type, **data)


class AuditLogger(EnhancedLogger):
    """Spezialisierter Logger für Audit-Trails"""
    
    @classmethod
    def log_access(cls, user: str, resource: str, action: str, result: str):
        """Logged einen Zugriff"""
        cls.audit(
            Category.AUDIT,
            f"Access: {action} on {resource}",
            user=user,
            resource=resource,
            action=action,
            result=result
        )
    
    @classmethod
    def log_change(cls, user: str, entity: str, changes: Dict[str, Any]):
        """Logged eine Änderung"""
        cls.audit(
            Category.AUDIT,
            f"Modified: {entity}",
            user=user,
            entity=entity,
            changes=changes
        )
    
    @classmethod
    def log_security_event(cls, event: str, severity: str, **details):
        """Logged ein Security-Event"""
        cls.security(
            Category.SECURITY,
            event,
            severity=severity,
            **details
        )


class PerformanceLogger(EnhancedLogger):
    """Spezialisierter Logger für Performance-Metriken"""
    
    @classmethod
    def log_metric(cls, 
                   name: str,
                   value: float,
                   unit: str = "ms",
                   tags: Optional[Dict[str, str]] = None):
        """Logged eine Performance-Metrik"""
        cls.metric(
            Category.METRICS,
            f"{name}: {value}{unit}",
            metric_name=name,
            metric_value=value,
            metric_unit=unit,
            tags=tags or {}
        )
    
    @classmethod
    def log_timing(cls, operation: str, duration: float):
        """Logged eine Timing-Messung"""
        cls.log_metric(operation, round(duration * 1000, 2), "ms")
    
    @classmethod
    def log_throughput(cls, operation: str, count: int, duration: float):
        """Logged Throughput-Metriken"""
        rate = count / duration if duration > 0 else 0
        cls.metric(
            Category.PERFORMANCE,
            f"{operation}: {count} ops in {duration:.2f}s",
            operation=operation,
            count=count,
            duration=duration,
            rate=round(rate, 2)
        )


# ==========================================
# INITIALIZATION
# ==========================================

# Auto-Initialize mit Standardwerten
def auto_init():
    """Automatische Initialisierung beim Import"""
    EnhancedLogger.initialize(
        min_level=LogLevel.INFO,
        console=True,
        console_colorized=True
    )

# Bei Import initialisieren
auto_init()

# Cleanup bei Programmende
atexit.register(EnhancedLogger.shutdown)


# ==========================================
# EXAMPLE USAGE
# ==========================================

if __name__ == "__main__":
    # Basis-Konfiguration
    logger.initialize(
        min_level=LogLevel.DEBUG,
        console=True,
        file_path=Path("logs/app.log"),
        async_mode=True
    )
    
    # Einfache Logs
    logger.info(Category.STARTUP, "Application starting...")
    logger.success(Category.SYSTEM, "Configuration loaded")
    logger.debug(Category.DEBUG, "Debug information", foo="bar")
    
    # Mit Context
    with logger.context("UserService"):
        logger.info(Category.AUTH, "User authentication started")
        logger.success(Category.AUTH, "User logged in", user_id=12345)
    
    # Mit Shortcuts
    logger.info(C.CORE.API, "API request received")
    logger.error(C.SEC.BASE, "Security violation detected")
    
    # Performance Messung
    with logger.measure(Category.DATABASE, "query_users"):
        time.sleep(0.1)  # Simulierte Operation
    
    # Exception Handling
    try:
        1 / 0
    except Exception as e:
        logger.error(Category.SYSTEM, "Critical error", exception=e)
    
    # Metriken abrufen
    metrics = logger.get_metrics()
    print(json.dumps(metrics, indent=2))
    
    # Structured Logging
    struct_logger = StructuredLogger()
    struct_logger.log_event(
        "user_action",
        Category.BUSINESS,
        "Order placed",
        order_id=1001,
        amount=99.99
    )
    
    # Audit Logging
    audit = AuditLogger()
    audit.log_access("john_doe", "/api/users", "READ", "SUCCESS")
    
    # Performance Logging
    perf = PerformanceLogger()
    perf.log_timing("api_response", 0.045)
    perf.log_throughput("requests", 1000, 10.5)
    
    # Cleanup
    logger.shutdown()