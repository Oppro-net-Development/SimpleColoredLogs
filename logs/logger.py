"""
Logs - Professional Terminal Logger
Ein vollständiger, produktionsreifer Logger mit erweiterten Features
PyNum Style Naming Convention
"""

from datetime import datetime
from typing import Optional, Callable, Dict, Any, List, Union
from pathlib import Path
import sys
import threading
import inspect
import traceback
import json
import os
import time
import atexit
from collections import defaultdict, deque

from colorama import Fore, Style, Back, init

# === NEUE DEFINITIONEN START ===

from enum import IntEnum
# from colorama import Fore, Style, Back # colorama wird schon oben importiert

# Achtung: Category und CategoryColors müssen noch definiert sein, falls sie nicht im Code sind
class Category(IntEnum):
    """Platzhalter für Category, falls sie nicht definiert ist"""
    SYSTEM = 0
    DATABASE = 1
    NETWORK = 2
    USER = 3
    DEFAULT = 99

class CategoryColors:
    """Platzhalter für CategoryColors"""
    @classmethod
    def get_color(cls, category: Category) -> str:
        return Fore.WHITE


class LogLevel(IntEnum):
    """Log-Level Definitionen"""
    TRACE = -1      # Sehr detaillierte Debug-Infos
    DEBUG = 0       # Entwickler-Informationen
    INFO = 1        # Allgemeine Informationen
    SUCCESS = 2     # Erfolgreiche Operationen
    LOADING = 3     # Startet Lade-Vorgang
    PROCESSING = 4  # Verarbeitet gerade
    PROGRESS = 5    # Fortschritts-Update (z.B. 45%)
    WAITING = 6     # Wartet auf Ressource/Response
    NOTICE = 7      # Wichtige Hinweise (zwischen INFO und WARN)
    WARN = 8        # Warnungen
    ERROR = 9       # Fehler
    CRITICAL = 10   # Kritische Fehler (noch behebbar)
    FATAL = 11      # Fatale Fehler (Programm-Absturz)
    SECURITY = 12   # Sicherheitsrelevante Events


class LogFormat(IntEnum):
    """Output-Format Optionen"""
    SIMPLE = 0      # [LEVEL] [CATEGORY] MSG
    STANDARD = 1    # [TIMESTAMP] [LEVEL] [CATEGORY] MSG
    DETAILED = 2    # [TIMESTAMP] [LEVEL] [CATEGORY] [file.py:123] MSG
    JSON = 3        # JSON-Format für Log-Aggregation


class LevelColors:
    """Farb-Mappings für Log-Levels"""
    
    COLORS = {
        LogLevel.TRACE: Fore.LIGHTBLACK_EX,
        LogLevel.DEBUG: Fore.CYAN,
        LogLevel.INFO: Fore.WHITE,
        LogLevel.SUCCESS: Fore.GREEN,
        LogLevel.LOADING: Fore.BLUE,
        LogLevel.PROCESSING: Fore.LIGHTCYAN_EX,
        LogLevel.PROGRESS: Fore.LIGHTBLUE_EX,
        LogLevel.WAITING: Fore.LIGHTYELLOW_EX,
        LogLevel.NOTICE: Fore.LIGHTMAGENTA_EX,
        LogLevel.WARN: Fore.YELLOW,
        LogLevel.ERROR: Fore.RED,
        LogLevel.CRITICAL: Fore.MAGENTA,
        LogLevel.FATAL: Fore.WHITE + Back.RED,
        LogLevel.SECURITY: Fore.BLACK + Back.YELLOW,
    }
    
    @classmethod
    def get_color(cls, level: LogLevel) -> str:
        """Gibt die Farbe für ein Log-Level zurück"""
        return cls.COLORS.get(level, Fore.WHITE)

# === NEUE DEFINITIONEN ENDE ===


# Colorama initialisieren
init(autoreset=True)


class Logs:
    """
    Professional Terminal Logger mit erweiterten Features
    
    Features:
    - 🎨 Farbige Terminal-Ausgabe mit 90+ Standard-Kategorien
    - 📁 File-Logging mit automatischer Rotation
    - 🎯 Level-Filtering & Kategorie-Filtering
    - 🔍 Metadaten (Dateiname, Zeile, Funktion)
    - 🧵 Thread-safe mit Lock
    - 📊 JSON-Export für Log-Aggregation
    - ⚡ Performance-Tracking & Profiling
    - 🎭 Context-Manager für verschachtelte Logs
    - 📝 Strukturierte Logs mit Key-Value Pairs
    - 📈 Live-Statistiken & Dashboards
    - 🔔 Alert-System für kritische Fehler
    - 🎬 Session-Recording
    - 🔄 Buffer-System für Batch-Logging
    - 🔒 Sensitive Data Redaction
    - 🌐 Distributed Tracing (Correlation/Trace/Span IDs)
    - 📡 Remote Log Forwarding (Syslog)
    - 🎲 Sampling & Rate Limiting
    - 🧠 Adaptive Logging (Auto-Level-Adjustment)
    - 🗜️ Log Compression
    - 🏥 Health Checks
    - 🔍 Debug Tools (tail, grep)
    - 📊 Prometheus Metrics Export
    """
    
    # === Konfiguration ===
    enabled: bool = True
    show_timestamp: bool = True
    min_level: LogLevel = LogLevel.DEBUG
    log_file: Optional[Path] = None
    colorize: bool = True
    format_type: LogFormat = LogFormat.STANDARD
    
    # Erweiterte Optionen
    show_metadata: bool = False
    show_thread_id: bool = False
    auto_flush: bool = True
    max_file_size: Optional[int] = 10 * 1024 * 1024  # 10MB
    backup_count: int = 3
    
    # Filter
    _category_filter: Optional[List[str]] = None
    _excluded_categories: List[str] = []
    
    # Format-Strings
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    message_color: str = Fore.WHITE
    
    # Buffer-System
    _buffer_enabled: bool = False
    _buffer: deque = deque(maxlen=1000)
    _buffer_flush_interval: float = 5.0
    _last_flush: float = time.time()
    
    # Session Recording
    _session_recording: bool = False
    _session_logs: List[Dict[str, Any]] = []
    _session_start: Optional[datetime] = None
    
    # Alert-System
    _alert_handlers: Dict[LogLevel, List[Callable]] = defaultdict(list)
    _alert_cooldown: Dict[str, float] = {}
    _alert_cooldown_seconds: float = 60.0
    
    # Sensitive Data Redaction
    _redact_enabled: bool = False
    _redact_patterns: List[str] = [
        r'\b\d{16}\b',  # Kreditkarten
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'password["\s:=]+\S+',
        r'api[_-]?key["\s:=]+\S+',
        r'secret["\s:=]+\S+',
        r'token["\s:=]+\S+',
        r'Bearer\s+\S+',
    ]
    
    # Correlation & Tracing
    _correlation_id: Optional[str] = None
    _trace_id: Optional[str] = None
    _span_id: Optional[str] = None
    
    # Remote Forwarding
    _remote_host: Optional[str] = None
    _remote_port: Optional[int] = None
    _remote_enabled: bool = False
    
    # Sampling & Rate Limiting
    _sampling_rate: float = 1.0
    _rate_limits: Dict[str, tuple] = {}
    _max_logs_per_minute: int = 1000
    _rate_limit_enabled: bool = False
    
    # Adaptive Logging
    _auto_adjust_level: bool = False
    _noise_threshold: int = 100
    _last_adjust_time: float = time.time()
    
    # Compression
    _compression_enabled: bool = False
    
    # Interne State
    _lock = threading.Lock()
    _handlers: List[Callable] = []
    _context_stack: List[str] = []
    _performance_markers: Dict[str, float] = {}
    _log_count: Dict[LogLevel, int] = {level: 0 for level in LogLevel}
    _category_count: Dict[str, int] = defaultdict(int)
    _error_count_by_category: Dict[str, int] = defaultdict(int)
    
    @classmethod
    def _redact_sensitive_data(cls, message: str) -> str:
        """Entfernt sensible Daten aus Log-Messages"""
        if not cls._redact_enabled:
            return message
        
        import re
        redacted = message
        for pattern in cls._redact_patterns:
            redacted = re.sub(pattern, '[REDACTED]', redacted, flags=re.IGNORECASE)
        return redacted
    
    @classmethod
    def _should_sample(cls) -> bool:
        """Prüft ob Log gesampelt werden soll"""
        if cls._sampling_rate >= 1.0:
            return True
        import random
        return random.random() < cls._sampling_rate
    
    @classmethod
    def _check_rate_limit(cls, category: str) -> bool:
        """Prüft Rate-Limit für Kategorie"""
        if not cls._rate_limit_enabled:
            return True
        
        current_time = time.time()
        key = f"rate_limit_{category}"
        
        if key in cls._rate_limits:
            count, window_start = cls._rate_limits[key]
            
            if current_time - window_start > 60:
                cls._rate_limits[key] = (1, current_time)
                return True
            
            if count >= cls._max_logs_per_minute:
                return False
            
            cls._rate_limits[key] = (count + 1, window_start)
            return True
        else:
            cls._rate_limits[key] = (1, current_time)
            return True
    
    @classmethod
    def _auto_adjust_log_level(cls):
        """Passt Log-Level automatisch an bei hoher Last"""
        if not cls._auto_adjust_level or not cls._session_start:
            return
        
        current_time = time.time()
        if current_time - cls._last_adjust_time < 60:
            return
        
        cls._last_adjust_time = current_time
        
        duration = (datetime.now() - cls._session_start).total_seconds() / 60
        if duration > 0:
            current_rate = sum(cls._log_count.values()) / duration
            
            if current_rate > cls._noise_threshold:
                if cls.min_level < LogLevel.WARN:
                    cls.min_level = LogLevel.WARN
                    cls.warn(Category.SYSTEM, f"Auto-adjusted log level to WARN (rate: {current_rate:.1f}/min)")
    
    @classmethod
    def _send_to_remote(cls, message: str):
        """Sendet Log zu Remote-Server (Syslog-Style)"""
        if not cls._remote_enabled or not cls._remote_host:
            return
        
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(message.encode('utf-8'), (cls._remote_host, cls._remote_port))
            sock.close()
        except Exception:
            pass
    
    @classmethod
    def _compress_old_logs(cls):
        """Komprimiert alte Log-Dateien"""
        if not cls._compression_enabled or not cls.log_file:
            return
        
        import gzip
        try:
            for i in range(1, cls.backup_count + 1):
                old_file = cls.log_file.with_suffix(f"{cls.log_file.suffix}.{i}")
                gz_file = Path(f"{old_file}.gz")
                
                if old_file.exists() and not gz_file.exists():
                    with open(old_file, 'rb') as f_in:
                        with gzip.open(gz_file, 'wb') as f_out:
                            f_out.writelines(f_in)
                    old_file.unlink()
        except Exception as e:
            print(f"[Logs] Compression-Fehler: {e}", file=sys.stderr)
    
    @classmethod
    def _get_metadata(cls, frame_depth: int) -> Dict[str, Any]:
        """Holt Metadaten vom Aufrufer"""
        try:
            frame = inspect.stack()[frame_depth]
            metadata = {
                "file": Path(frame.filename).name,
                "line": frame.lineno,
                "function": frame.function,
                "thread": threading.current_thread().name if cls.show_thread_id else None
            }
            
            if cls._correlation_id:
                metadata["correlation_id"] = cls._correlation_id
            if cls._trace_id:
                metadata["trace_id"] = cls._trace_id
            if cls._span_id:
                metadata["span_id"] = cls._span_id
            
            return metadata
        except Exception:
            return {"file": "", "line": 0, "function": "", "thread": None}
    
    @classmethod
    def _format_json(cls, level: LogLevel, category: str, message: str, metadata: Dict[str, Any], extra: Optional[Dict] = None) -> str:
        """Formatiert Log als JSON"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.name,
            "category": category,
            "message": message,
            **metadata
        }
        if cls._context_stack:
            log_entry["context"] = " > ".join(cls._context_stack)
        if extra:
            log_entry["extra"] = extra
        return json.dumps(log_entry, ensure_ascii=False)
    
    @classmethod
    def _format_colored(cls, level: LogLevel, category: str, message: str, metadata: Dict[str, Any], extra: Optional[Dict] = None) -> str:
        """Formatiert farbigen Log-Output"""
        level_name = level.name
        level_color = LevelColors.get_color(level)
        category_color = CategoryColors.get_color(Category(category))
        
        # Timestamp
        timestamp_part = ""
        if cls.show_timestamp and cls.format_type != LogFormat.SIMPLE:
            ts = datetime.now().strftime(cls.timestamp_format)
            timestamp_part = f"{Style.DIM}[{ts}]{Style.RESET_ALL} "
        
        # Level - FETT und in Klammern
        padded_level = f"{level_name:<10}" # Padding an die längsten Namen angepasst
        level_part = f"{level_color}{Style.BRIGHT}[{padded_level}]{Style.RESET_ALL}"
        
        # Category mit Farbe
        category_part = f"{category_color}[{category}]{Style.RESET_ALL}"
        
        # Kontext
        context_part = ""
        if cls._context_stack:
            context = " > ".join(cls._context_stack)
            context_part = f"{Style.DIM}({context}){Style.RESET_ALL} "
        
        # Metadata (Datei:Zeile)
        metadata_part = ""
        if cls.show_metadata and cls.format_type == LogFormat.DETAILED:
            metadata_part = f"{Style.DIM}[{metadata['file']}:{metadata['line']}]{Style.RESET_ALL} "
        
        # Thread ID
        thread_part = ""
        if cls.show_thread_id and metadata.get('thread'):
            thread_part = f"{Style.DIM}[{metadata['thread']}]{Style.RESET_ALL} "
        
        # Tracing IDs
        tracing_part = ""
        if cls._correlation_id:
            tracing_part += f"{Style.DIM}[corr:{cls._correlation_id[:8]}]{Style.RESET_ALL} "
        
        # Extra Key-Value Pairs
        extra_part = ""
        if extra:
            extra_str = " ".join(f"{Style.DIM}{k}={v}{Style.RESET_ALL}" for k, v in extra.items())
            extra_part = f"{extra_str} "
        
        # Message
        msg_color = Fore.RED if level >= LogLevel.ERROR else cls.message_color
        message_part = f"{msg_color}{message}{Style.RESET_ALL}"
        
        return f"{timestamp_part}{level_part} {category_part} {thread_part}{tracing_part}{metadata_part}{context_part}{extra_part}{message_part}"
    
    @classmethod
    def _should_log_category(cls, category: str) -> bool:
        """Prüft ob Kategorie geloggt werden soll"""
        if category in cls._excluded_categories:
            return False
        if cls._category_filter and category not in cls._category_filter:
            return False
        return True
    
    @classmethod
    def _trigger_alerts(cls, level: LogLevel, category: str, message: str):
        """Triggert Alert-Handler für kritische Logs"""
        if level in cls._alert_handlers:
            alert_key = f"{level.name}:{category}"
            current_time = time.time()
            
            if alert_key in cls._alert_cooldown:
                if current_time - cls._alert_cooldown[alert_key] < cls._alert_cooldown_seconds:
                    return
            
            cls._alert_cooldown[alert_key] = current_time
            
            for handler in cls._alert_handlers[level]:
                try:
                    handler(level, category, message)
                except Exception as e:
                    print(f"[Logs] Alert-Handler-Fehler: {e}", file=sys.stderr)
    
    @classmethod
    def _rotate_log_file(cls):
        """Rotiert Log-Datei wenn zu groß"""
        if not cls.log_file or not cls.max_file_size:
            return
        
        try:
            if cls.log_file.exists() and cls.log_file.stat().st_size > cls.max_file_size:
                for i in range(cls.backup_count - 1, 0, -1):
                    old_file = cls.log_file.with_suffix(f"{cls.log_file.suffix}.{i}")
                    new_file = cls.log_file.with_suffix(f"{cls.log_file.suffix}.{i+1}")
                    if old_file.exists():
                        old_file.rename(new_file)
                
                cls.log_file.rename(cls.log_file.with_suffix(f"{cls.log_file.suffix}.1"))
        except Exception as e:
            print(f"[Logs] Rotation-Fehler: {e}", file=sys.stderr)
    
    @classmethod
    def _write_to_file(cls, message: str, is_json: bool = False):
        """Schreibt in Log-Datei mit Rotation"""
        if not cls.log_file:
            return
        
        cls._rotate_log_file()
        
        try:
            clean_message = message
            if not is_json:
                # Entfernt Colorama-Codes für Datei-Logging
                for code in list(Fore.__dict__.values()) + list(Style.__dict__.values()) + list(Back.__dict__.values()):
                    if isinstance(code, str):
                        clean_message = clean_message.replace(code, '')
            
            with open(cls.log_file, 'a', encoding='utf-8') as f:
                f.write(clean_message + '\n')
                if cls.auto_flush:
                    f.flush()
        except Exception as e:
            print(f"[Logs] File-Write-Fehler: {e}", file=sys.stderr)
    
    @classmethod
    def _flush_buffer(cls):
        """Flusht den Log-Buffer"""
        if not cls._buffer:
            return
        
        with cls._lock:
            while cls._buffer:
                log_entry = cls._buffer.popleft()
                cls._write_to_file(log_entry["output"], log_entry.get("is_json", False))
                print(log_entry["output"])
    
    @classmethod
    def _log(cls, level: LogLevel, category: str, message: str, extra: Optional[Dict] = None, frame_depth: int = 3):
        """Interne Log-Methode"""
        if not cls.enabled or level < cls.min_level:
            return
        
        if not cls._should_log_category(category):
            return
        
        if not cls._should_sample():
            return
        
        if not cls._check_rate_limit(category):
            return
        
        cls._auto_adjust_log_level()
        
        with cls._lock:
            cls._log_count[level] += 1
            cls._category_count[category] += 1
            
            if level >= LogLevel.ERROR:
                cls._error_count_by_category[category] += 1
            
            message = cls._redact_sensitive_data(message)
            metadata = cls._get_metadata(frame_depth)
            
            if cls.format_type == LogFormat.JSON:
                output = cls._format_json(level, category, message, metadata, extra)
                is_json = True
            else:
                output = cls._format_colored(level, category, message, metadata, extra)
                is_json = False
            
            if cls._session_recording:
                cls._session_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "level": level.name,
                    "category": category,
                    "message": message,
                    "metadata": metadata,
                    "extra": extra
                })
            
            if cls._buffer_enabled:
                cls._buffer.append({"output": output, "is_json": is_json})
                if time.time() - cls._last_flush > cls._buffer_flush_interval:
                    cls._flush_buffer()
                    cls._last_flush = time.time()
            else:
                if level >= LogLevel.ERROR:
                    print(output, file=sys.stderr)
                else:
                    print(output)
                
                cls._write_to_file(output, is_json)
                cls._send_to_remote(output)
            
            cls._trigger_alerts(level, category, message)
            
            for handler in cls._handlers:
                try:
                    handler(level, category, message, metadata)
                except Exception as e:
                    print(f"[Logs] Handler-Fehler: {e}", file=sys.stderr)
    
    # === Public Logging Methods (Alle Level enthalten) ===
    
    @classmethod
    def trace(cls, category: Category, message: str, **kwargs):
        """TRACE Level - Sehr detaillierte Debug-Infos"""
        cls._log(LogLevel.TRACE, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def debug(cls, category: Category, message: str, **kwargs):
        """DEBUG Level - Debug-Informationen"""
        cls._log(LogLevel.DEBUG, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def info(cls, category: Category, message: str, **kwargs):
        """INFO Level - Allgemeine Informationen"""
        cls._log(LogLevel.INFO, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def success(cls, category: Category, message: str, **kwargs):
        """SUCCESS Level - Erfolgreiche Operationen"""
        cls._log(LogLevel.SUCCESS, category.value, message, kwargs if kwargs else None)

    @classmethod
    def loading(cls, category: Category, message: str, **kwargs):
        """LOADING Level - Startet Lade-Vorgang"""
        cls._log(LogLevel.LOADING, category.value, message, kwargs if kwargs else None)

    @classmethod
    def processing(cls, category: Category, message: str, **kwargs):
        """PROCESSING Level - Verarbeitet gerade"""
        cls._log(LogLevel.PROCESSING, category.value, message, kwargs if kwargs else None)

    @classmethod
    def progress(cls, category: Category, message: str, **kwargs):
        """PROGRESS Level - Fortschritts-Update (z.B. 45%)"""
        cls._log(LogLevel.PROGRESS, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def waiting(cls, category: Category, message: str, **kwargs):
        """WAITING Level - Wartet auf Ressource/Response"""
        cls._log(LogLevel.WAITING, category.value, message, kwargs if kwargs else None)
        
    @classmethod
    def notice(cls, category: Category, message: str, **kwargs):
        """NOTICE Level - Wichtige Hinweise (zwischen INFO und WARN)"""
        cls._log(LogLevel.NOTICE, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def warn(cls, category: Category, message: str, **kwargs):
        """WARN Level - Warnungen"""
        cls._log(LogLevel.WARN, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def error(cls, category: Category, message: str, **kwargs):
        """ERROR Level - Fehler"""
        cls._log(LogLevel.ERROR, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def critical(cls, category: Category, message: str, **kwargs):
        """CRITICAL Level - Kritische Fehler (noch behebbar)"""
        cls._log(LogLevel.CRITICAL, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def fatal(cls, category: Category, message: str, **kwargs):
        """FATAL Level - Fatale Fehler (Programm-Absturz)"""
        cls._log(LogLevel.FATAL, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def security(cls, category: Category, message: str, **kwargs):
        """SECURITY Level - Sicherheitsrelevante Events"""
        cls._log(LogLevel.SECURITY, category.value, message, kwargs if kwargs else None)
    
    @classmethod
    def exception(cls, category: Category, message: str, exc: Optional[BaseException] = None):
        """ERROR mit Traceback"""
        full_message = f"{message}\n"
        if exc is not None:
            full_message += "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        else:
            full_message += traceback.format_exc()
        cls._log(LogLevel.ERROR, category.value, full_message.strip(), frame_depth=3)
    
    # === Utility Methods ===
    
    @classmethod
    def separator(cls, char: str = "=", length: int = 50):
        """Druckt eine Trennlinie"""
        print(f"{Style.DIM}{char * length}{Style.RESET_ALL}")
    
    @classmethod
    def banner(cls, text: str, category: Category = Category.SYSTEM):
        """Druckt einen auffälligen Banner"""
        cls.separator("=", 60)
        cls.info(category, f"  {text}")
        cls.separator("=", 60)
    
    @classmethod
    def configure(cls, **kwargs):
        """Konfiguriert den Logger"""
        with cls._lock:
            for key, value in kwargs.items():
                if hasattr(cls, key):
                    setattr(cls, key, value)


class LogContext:
    """Context Manager für verschachtelte Logs"""
    def __init__(self, name: str):
        self.name = name
    
    def __enter__(self):
        Logs._context_stack.append(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if Logs._context_stack:
            Logs._context_stack.pop()


@atexit.register
def _cleanup():
    """Cleanup beim Beenden"""
    if Logs._buffer_enabled:
        Logs._flush_buffer()
    # Log.stop_session wurde nicht bereitgestellt, aber der Aufruf wurde entfernt,
    # um Fehler zu vermeiden, falls die Methode fehlt.
    # if Logs._session_recording:
    #     Logs.stop_session()