"""
Configuration settings for Survey AI Agent
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class GeminiConfig:
    """Configuration for Google Gemini API"""
    api_key: str
    model_name: str = "gemini-2.5-flash-lite"
    temperature: float = 0.7
    max_tokens: int = 1000

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create GeminiConfig from environment variables"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "1000")),
        )


@dataclass
class SheetsConfig:
    """Configuration for Google Sheets API"""
    credentials_path: str
    default_sheet_name: str = "Survey_Responses"
    data_range: str = "A:Z"

    @classmethod
    def from_env(cls) -> "SheetsConfig":
        """Create SheetsConfig from environment variables"""
        credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
        if not credentials_path:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS_PATH environment variable is required")
        
        return cls(
            credentials_path=credentials_path,
            default_sheet_name=os.getenv("DEFAULT_SHEET_NAME", "Survey_Responses"),
            data_range=os.getenv("DATA_RANGE", "A:Z"),
        )


@dataclass
class SurveyConfig:
    """Configuration for survey behavior"""
    default_question_count: int = 10
    max_conversation_history: int = 50
    answer_validation_timeout: int = 30
    debug: bool = False
    environment: str = "production"

    @classmethod
    def from_env(cls) -> "SurveyConfig":
        """Create SurveyConfig from environment variables"""
        return cls(
            default_question_count=int(os.getenv("DEFAULT_QUESTION_COUNT", "10")),
            max_conversation_history=int(os.getenv("MAX_CONVERSATION_HISTORY", "50")),
            answer_validation_timeout=int(os.getenv("ANSWER_VALIDATION_TIMEOUT", "30")),
            debug=os.getenv("DEBUG", "False").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "production"),
        )


@dataclass
class AppConfig:
    """Main application configuration"""
    gemini: GeminiConfig
    sheets: SheetsConfig
    survey: SurveyConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create AppConfig from environment variables"""
        return cls(
            gemini=GeminiConfig.from_env(),
            sheets=SheetsConfig.from_env(),
            survey=SurveyConfig.from_env(),
        )


# Global configuration instance
def get_config() -> AppConfig:
    """Get the application configuration"""
    return AppConfig.from_env()