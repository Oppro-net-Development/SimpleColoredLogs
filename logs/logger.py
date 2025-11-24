"""
logger.py

Professional Terminal Logger mit erweiterten Features
Ein vollständiger, produktionsreifer Logger, der log_categories.py importiert.
"""

from datetime import datetime
from typing import Optional, Callable, Dict, Any, List, Union, ClassVar
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
from enum import IntEnum, Enum

from colorama import Fore, Style, Back, init

# WICHTIG: Kategorien aus der separaten Datei importieren
from .category import Category, CategoryColors 

# Colorama initialisieren
init(autoreset=True)


## 🚀 LOG LEVEL DEFINITIONEN

class LogLevel(IntEnum):
    """Log-Level Definitionen"""
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


## 💻 LOGS HAUPTKLASSE

class Logs:
    """
    Professional Terminal Logger mit erweiterten Features
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
            # frame_depth = 4, da 0=inspect.stack, 1=_get_metadata, 2=_log, 3=public_method, 4=caller
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
    def _format_json(cls, level: LogLevel, category: Category, message: str, metadata: Dict[str, Any], extra: Optional[Dict] = None) -> str:
        """Formatiert Log als JSON"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.name,
            "category": category.value, # Kategorie als String-Wert
            "message": message,
            **metadata
        }
        if cls._context_stack:
            log_entry["context"] = " > ".join(cls._context_stack)
        if extra:
            log_entry["extra"] = extra
        return json.dumps(log_entry, ensure_ascii=False)
    
    @classmethod
    def _format_colored(cls, level: LogLevel, category: Category, message: str, metadata: Dict[str, Any], extra: Optional[Dict] = None) -> str:
        """Formatiert farbigen Log-Output"""
        level_name = level.name
        level_color = LevelColors.get_color(level)
        
        # Kategorie Farbe aus importierter Klasse
        category_color = CategoryColors.get_color(category) 
        
        # Timestamp
        timestamp_part = ""
        if cls.show_timestamp and cls.format_type != LogFormat.SIMPLE:
            ts = datetime.now().strftime(cls.timestamp_format)
            timestamp_part = f"{Style.DIM}[{ts}]{Style.RESET_ALL} "
        
        # Level - FETT und in Klammern
        padded_level = f"{level_name:<10}"
        level_part = f"{level_color}{Style.BRIGHT}[{padded_level}]{Style.RESET_ALL}"
        
        # Category mit Farbe
        category_part = f"{category_color}[{category.value}]{Style.RESET_ALL}"
        
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
    def _should_log_category(cls, category: Category) -> bool:
        """Prüft ob Kategorie geloggt werden soll"""
        category_str = category.value
        if category_str in cls._excluded_categories:
            return False
        if cls._category_filter and category_str not in cls._category_filter:
            return False
        return True
    
    @classmethod
    def _trigger_alerts(cls, level: LogLevel, category: Category, message: str):
        """Triggert Alert-Handler für kritische Logs"""
        if level in cls._alert_handlers:
            alert_key = f"{level.name}:{category.value}"
            current_time = time.time()
            
            if alert_key in cls._alert_cooldown:
                if current_time - cls._alert_cooldown[alert_key] < cls._alert_cooldown_seconds:
                    return
            
            cls._alert_cooldown[alert_key] = current_time
            
            for handler in cls._alert_handlers[level]:
                try:
                    handler(level, category.value, message)
                except Exception as e:
                    print(f"[Logs] Alert-Handler-Fehler: {e}", file=sys.stderr)
    
    @classmethod
    def _log(cls, level: LogLevel, category: Category, message: str, extra: Optional[Dict] = None, frame_depth: int = 3):
        """Die zentrale Log-Methode"""
        
        if not cls.enabled or level < cls.min_level:
            return
        
        if not cls._should_log_category(category):
            return
            
        if not cls._should_sample():
            return
            
        if not cls._check_rate_limit(category.value):
            return
            
        cls._auto_adjust_log_level()
        
        with cls._lock:
            # 1. Metadaten sammeln
            metadata = cls._get_metadata(frame_depth=frame_depth + 1) # +1 für diesen Aufruf
            
            # 2. Nachricht bearbeiten
            message = cls._redact_sensitive_data(message)
            
            # 3. Formatieren
            if cls.format_type == LogFormat.JSON:
                formatted_message = cls._format_json(level, category, message, metadata, extra)
            else:
                formatted_message = cls._format_colored(level, category, message, metadata, extra)
            
            # 4. Speichern und Ausgeben
            cls._output(formatted_message, level)
            
            # 5. Zähler und Speicherung aktualisieren
            cls._log_count[level] += 1
            cls._category_count[category.value] += 1
            if level >= LogLevel.ERROR:
                cls._error_count_by_category[category.value] += 1
            
            # 6. Session Recording
            if cls._session_recording:
                cls._session_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "level": level.name,
                    "category": category.value,
                    "message": message,
                    **metadata
                })
            
            # 7. Alerts und Weiterleitung
            cls._trigger_alerts(level, category, message)
            if cls._remote_enabled:
                cls._send_to_remote(formatted_message)
    
    @classmethod
    def _output(cls, message: str, level: LogLevel):
        """Schreibt die Nachricht in die Konsole und in die Datei"""
        
        # Konsole
        if cls.colorize:
            print(message, file=sys.stderr if level >= LogLevel.WARN else sys.stdout)
        else:
            # Entferne alle ANSI-Codes für nicht-farbige Ausgabe
            import re
            message_stripped = re.sub(r'\x1b\[[0-9;]*m', '', message)
            print(message_stripped, file=sys.stderr if level >= LogLevel.WARN else sys.stdout)
        
        # Datei-Log (gepuffert oder direkt)
        if cls.log_file:
            log_line = cls._format_json(level, Category(level.name) if level.name in Category.__members__ else Category.SYSTEM, message, cls._get_metadata(frame_depth=5)) # Frame depth angepasst
            
            if cls._buffer_enabled:
                cls._buffer.append(log_line)
                if time.time() - cls._last_flush > cls._buffer_flush_interval:
                    cls._flush_buffer()
            else:
                cls._write_to_file(f"{log_line}\n")
    
    @classmethod
    def _write_to_file(cls, data: str):
        """Führt die eigentliche Schreiboperation durch und prüft die Dateigröße"""
        if not cls.log_file:
            return

        try:
            # Log-Rotation prüfen
            if cls.max_file_size and cls.log_file.exists() and cls.log_file.stat().st_size > cls.max_file_size:
                cls._rotate_logs()
                
            with open(cls.log_file, 'a', encoding='utf-8') as f:
                f.write(data)
                if cls.auto_flush:
                    f.flush()
        except Exception as e:
            print(f"[Logs] Dateischreibfehler: {e}", file=sys.stderr)

    @classmethod
    def _rotate_logs(cls):
        """Rotiert Log-Dateien, wenn die maximale Größe erreicht ist"""
        if not cls.log_file:
            return
        
        # Älteste Datei löschen
        if cls.backup_count > 0:
            oldest_file = cls.log_file.with_suffix(f"{cls.log_file.suffix}.{cls.backup_count}")
            if oldest_file.exists():
                oldest_file.unlink()
            
            # Dateien verschieben (n -> n+1)
            for i in range(cls.backup_count - 1, 0, -1):
                src = cls.log_file.with_suffix(f"{cls.log_file.suffix}.{i}")
                dst = cls.log_file.with_suffix(f"{cls.log_file.suffix}.{i+1}")
                if src.exists():
                    src.rename(dst)
            
            # Aktuelle Datei umbenennen zu .1
            cls.log_file.rename(cls.log_file.with_suffix(f"{cls.log_file.suffix}.1"))
            
        cls.info(Category.SYSTEM, f"Logdatei rotiert: {cls.log_file.name}")
        cls._compress_old_logs()

    @classmethod
    def _flush_buffer(cls):
        """Schreibt den Puffer in die Logdatei"""
        if not cls._buffer_enabled or not cls.log_file or not cls._buffer:
            return
        
        with cls._lock:
            buffer_copy = list(cls._buffer)
            cls._buffer.clear()
            cls._write_to_file("\n".join(buffer_copy) + "\n")
            cls._last_flush = time.time()
    
    # === Public Logging Methoden ===

    @classmethod
    def trace(cls, category: Category, message: str, **kwargs):
        """Trace-Level Log (sehr detailliert)"""
        cls._log(LogLevel.TRACE, category, message, extra=kwargs, frame_depth=3)
        
    @classmethod
    def debug(cls, category: Category, message: str, **kwargs):
        """Debug-Level Log"""
        cls._log(LogLevel.DEBUG, category, message, extra=kwargs, frame_depth=3)

    @classmethod
    def info(cls, category: Category, message: str, **kwargs):
        """Info-Level Log"""
        cls._log(LogLevel.INFO, category, message, extra=kwargs, frame_depth=3)

    @classmethod
    def success(cls, category: Category, message: str, **kwargs):
        """Success-Level Log"""
        cls._log(LogLevel.SUCCESS, category, message, extra=kwargs, frame_depth=3)
        
    @classmethod
    def loading(cls, category: Category, message: str, **kwargs):
        """Loading-Level Log"""
        cls._log(LogLevel.LOADING, category, message, extra=kwargs, frame_depth=3)
        
    @classmethod
    def processing(cls, category: Category, message: str, **kwargs):
        """Processing-Level Log"""
        cls._log(LogLevel.PROCESSING, category, message, extra=kwargs, frame_depth=3)

    @classmethod
    def progress(cls, category: Category, message: str, **kwargs):
        """Progress-Level Log"""
        cls._log(LogLevel.PROGRESS, category, message, extra=kwargs, frame_depth=3)
        
    @classmethod
    def waiting(cls, category: Category, message: str, **kwargs):
        """Waiting-Level Log"""
        cls._log(LogLevel.WAITING, category, message, extra=kwargs, frame_depth=3)
        
    @classmethod
    def notice(cls, category: Category, message: str, **kwargs):
        """Notice-Level Log"""
        cls._log(LogLevel.NOTICE, category, message, extra=kwargs, frame_depth=3)

    @classmethod
    def warn(cls, category: Category, message: str, **kwargs):
        """Warn-Level Log"""
        cls._log(LogLevel.WARN, category, message, extra=kwargs, frame_depth=3)

    @classmethod
    def error(cls, category: Category, message: str, exception: Optional[BaseException] = None, **kwargs):
        """Error-Level Log mit optionaler Exception-Verarbeitung"""
        if exception:
            trace = traceback.format_exc()
            message = f"{message} (Exception: {type(exception).__name__}: {exception})\n{trace}"
        cls._log(LogLevel.ERROR, category, message, extra=kwargs, frame_depth=3)

    @classmethod
    def critical(cls, category: Category, message: str, exception: Optional[BaseException] = None, **kwargs):
        """Critical-Level Log"""
        if exception:
            trace = traceback.format_exc()
            message = f"{message} (Exception: {type(exception).__name__}: {exception})\n{trace}"
        cls._log(LogLevel.CRITICAL, category, message, extra=kwargs, frame_depth=3)
        
    @classmethod
    def fatal(cls, category: Category, message: str, exception: Optional[BaseException] = None, **kwargs):
        """Fatal-Level Log"""
        if exception:
            trace = traceback.format_exc()
            message = f"{message} (Exception: {type(exception).__name__}: {exception})\n{trace}"
        cls._log(LogLevel.FATAL, category, message, extra=kwargs, frame_depth=3)

    @classmethod
    def security(cls, category: Category, message: str, **kwargs):
        """Security-Level Log"""
        cls._log(LogLevel.SECURITY, category, message, extra=kwargs, frame_depth=3)
    
    # === Kontext-Management ===
    
    @classmethod
    def push_context(cls, context: str):
        """Fügt einen Kontext-String zum Stack hinzu"""
        cls._context_stack.append(context)
        
    @classmethod
    def pop_context(cls):
        """Entfernt den obersten Kontext-String vom Stack"""
        if cls._context_stack:
            return cls._context_stack.pop()
        return None
    
    # === Konfigurationsmethoden ===
    
    @classmethod
    def configure(cls, 
                  min_level: LogLevel = LogLevel.DEBUG, 
                  log_file: Optional[Union[str, Path]] = None,
                  format_type: LogFormat = LogFormat.STANDARD,
                  show_metadata: bool = False,
                  show_thread_id: bool = False,
                  enable_buffer: bool = False,
                  enable_redaction: bool = False,
                  enable_remote: bool = False,
                  remote_host: Optional[str] = None,
                  remote_port: int = 514,
                  category_filter: Optional[List[Category]] = None,
                  exclude_categories: Optional[List[Category]] = None,
                  sampling_rate: float = 1.0
                  ):
        """Konfiguriert den Logger mit zentralen Einstellungen."""
        
        with cls._lock:
            cls.min_level = min_level
            cls.format_type = format_type
            cls.show_metadata = show_metadata
            cls.show_thread_id = show_thread_id
            cls._buffer_enabled = enable_buffer
            cls._redact_enabled = enable_redaction
            cls._remote_enabled = enable_remote
            cls._remote_host = remote_host
            cls._remote_port = remote_port
            cls._sampling_rate = max(0.0, min(1.0, sampling_rate))
            
            if log_file:
                cls.log_file = Path(log_file) if isinstance(log_file, str) else log_file
                if cls.log_file.parent:
                    cls.log_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                cls.log_file = None
                
            if category_filter:
                cls._category_filter = [c.value for c in category_filter]
            else:
                cls._category_filter = None
                
            if exclude_categories:
                cls._excluded_categories = [c.value for c in exclude_categories]
            else:
                cls._excluded_categories = []
    
    @classmethod
    def register_alert_handler(cls, level: LogLevel, handler: Callable):
        """Registriert einen Handler, der bei einem bestimmten LogLevel ausgelöst wird."""
        cls._alert_handlers[level].append(handler)
        
    @classmethod
    def start_session_recording(cls):
        """Startet die Aufzeichnung von Logs im Speicher."""
        with cls._lock:
            cls._session_recording = True
            cls._session_logs = []
            cls._session_start = datetime.now()
            cls.info(Category.SYSTEM, "Session-Recording gestartet.")
            
    @classmethod
    def stop_session_recording(cls) -> List[Dict[str, Any]]:
        """Stoppt die Aufzeichnung und gibt die gesammelten Logs zurück."""
        with cls._lock:
            if cls._session_recording:
                cls._session_recording = False
                cls.info(Category.SYSTEM, f"Session-Recording beendet. {len(cls._session_logs)} Einträge gesammelt.")
                return cls._session_logs
            return []

# Registriere atexit-Funktion, um den Puffer beim Beenden zu leeren
atexit.register(Logs._flush_buffer)