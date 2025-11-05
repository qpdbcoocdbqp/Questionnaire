"""
Configuration models for the Survey AI Agent.

This module contains configuration classes for various services and components.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import os


@dataclass
class GeminiConfig:
    """Configuration for Google Gemini API."""
    
    api_key: str = ""
    model_name: str = "gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout_seconds: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate Gemini configuration."""
        if not self.api_key:
            # Try to get from environment variable
            self.api_key = os.getenv('GEMINI_API_KEY', '')
            if not self.api_key:
                raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or provide api_key.")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeminiConfig':
        """Create GeminiConfig from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> 'GeminiConfig':
        """Create GeminiConfig from environment variables."""
        return cls(
            api_key=os.getenv('GEMINI_API_KEY', ''),
            model_name=os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash-lite'),
            temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.7')),
            max_tokens=int(os.getenv('GEMINI_MAX_TOKENS', '1000')),
            timeout_seconds=int(os.getenv('GEMINI_TIMEOUT_SECONDS', '30')),
            max_retries=int(os.getenv('GEMINI_MAX_RETRIES', '3'))
        )


@dataclass
class SheetsConfig:
    """Configuration for Google Sheets API."""
    credentials_path: str = ""
    google_drive_folder_id: Optional[str] = None
    default_sheet_name: str = "Survey Responses"
    data_range: str = "A:Z"
    timeout_seconds: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate Sheets configuration."""
        if not self.credentials_path:
            # Try to get from environment variable
            self.credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', '')
            self.google_drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

            if not self.credentials_path:
                raise ValueError("Google Sheets credentials path is required. Set GOOGLE_SHEETS_CREDENTIALS_PATH environment variable or provide credentials_path.")
        
        if not os.path.exists(self.credentials_path):
            raise ValueError(f"Credentials file not found: {self.credentials_path}")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SheetsConfig':
        """Create SheetsConfig from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> 'SheetsConfig':
        """Create SheetsConfig from environment variables."""
        return cls(
            credentials_path=os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', ''),
            google_drive_folder_id=os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
            default_sheet_name=os.getenv('SHEETS_DEFAULT_NAME', 'Survey Responses'),
            data_range=os.getenv('SHEETS_DATA_RANGE', 'A:Z'),
            timeout_seconds=int(os.getenv('SHEETS_TIMEOUT_SECONDS', '30')),
            max_retries=int(os.getenv('SHEETS_MAX_RETRIES', '3'))
        )


@dataclass
class AgentConfig:
    """Main configuration for the Survey AI Agent."""
    
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    sheets: SheetsConfig = field(default_factory=SheetsConfig)
    debug_mode: bool = False
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate agent configuration."""
        self.gemini.validate()
        self.sheets.validate()
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"log_level must be one of: {valid_log_levels}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'gemini': self.gemini.to_dict(),
            'sheets': self.sheets.to_dict(),
            'debug_mode': self.debug_mode,
            'log_level': self.log_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create AgentConfig from dictionary."""
        gemini_data = data.get('gemini', {})
        sheets_data = data.get('sheets', {})
        
        return cls(
            gemini=GeminiConfig.from_dict(gemini_data),
            sheets=SheetsConfig.from_dict(sheets_data),
            debug_mode=data.get('debug_mode', False),
            log_level=data.get('log_level', 'INFO')
        )
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Create AgentConfig from environment variables."""
        return cls(
            gemini=GeminiConfig.from_env(),
            sheets=SheetsConfig.from_env(),
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )