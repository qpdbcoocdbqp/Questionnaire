"""
Custom exception classes for the Survey AI Agent.

This module defines all custom exceptions used throughout the application
with proper error handling and context information.
"""

from typing import Any, Optional


class SurveyError(Exception):
    """Base exception class for all survey-related errors."""
    
    def __init__(self, message: str, context: Optional[dict] = None):
        """
        Initialize SurveyError.
        
        Args:
            message: Error message
            context: Additional context information
        """
        self.message = message
        self.context = context or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class ValidationError(SurveyError):
    """Exception raised when data validation fails."""
    
    def __init__(self, field: str, value: Any, message: str, context: Optional[dict] = None):
        """
        Initialize ValidationError.
        
        Args:
            field: Name of the field that failed validation
            value: The invalid value
            message: Validation error message
            context: Additional context information
        """
        self.field = field
        self.value = value
        
        full_message = f"Validation failed for field '{field}': {message}"
        if value is not None:
            full_message += f" (value: {value})"
        
        context = context or {}
        context.update({'field': field, 'value': value})
        
        super().__init__(full_message, context)


class APIError(SurveyError):
    """Exception raised when external API calls fail."""
    
    def __init__(self, service: str, message: str, status_code: Optional[int] = None, 
                 retry_after: Optional[int] = None, context: Optional[dict] = None):
        """
        Initialize APIError.
        
        Args:
            service: Name of the service that failed (e.g., 'Gemini', 'Google Sheets')
            message: Error message from the API
            status_code: HTTP status code if applicable
            retry_after: Seconds to wait before retrying
            context: Additional context information
        """
        self.service = service
        self.status_code = status_code
        self.retry_after = retry_after
        
        full_message = f"{service} API error: {message}"
        if status_code:
            full_message += f" (Status: {status_code})"
        
        context = context or {}
        context.update({
            'service': service,
            'status_code': status_code,
            'retry_after': retry_after
        })
        
        super().__init__(full_message, context)
    
    @property
    def is_retryable(self) -> bool:
        """Check if this error is retryable based on status code."""
        if self.status_code is None:
            return True  # Network errors are generally retryable
        
        # Retryable HTTP status codes
        retryable_codes = {429, 500, 502, 503, 504}
        return self.status_code in retryable_codes


class ConfigurationError(SurveyError):
    """Exception raised when configuration is invalid or missing."""
    
    def __init__(self, config_key: str, message: str, context: Optional[dict] = None):
        """
        Initialize ConfigurationError.
        
        Args:
            config_key: Name of the configuration key that's invalid
            message: Configuration error message
            context: Additional context information
        """
        self.config_key = config_key
        
        full_message = f"Configuration error for '{config_key}': {message}"
        
        context = context or {}
        context.update({'config_key': config_key})
        
        super().__init__(full_message, context)


class ConversationError(SurveyError):
    """Exception raised during conversation flow errors."""
    
    def __init__(self, message: str, user_id: Optional[str] = None, 
                 question_id: Optional[str] = None, context: Optional[dict] = None):
        """
        Initialize ConversationError.
        
        Args:
            message: Error message
            user_id: ID of the user involved in the conversation
            question_id: ID of the question being processed
            context: Additional context information
        """
        self.user_id = user_id
        self.question_id = question_id
        
        context = context or {}
        if user_id:
            context['user_id'] = user_id
        if question_id:
            context['question_id'] = question_id
        
        super().__init__(message, context)


class DataStorageError(SurveyError):
    """Exception raised when data storage operations fail."""
    
    def __init__(self, operation: str, message: str, storage_type: str = "unknown",
                 context: Optional[dict] = None):
        """
        Initialize DataStorageError.
        
        Args:
            operation: The storage operation that failed (e.g., 'write', 'read', 'delete')
            message: Error message
            storage_type: Type of storage (e.g., 'Google Sheets', 'local file')
            context: Additional context information
        """
        self.operation = operation
        self.storage_type = storage_type
        
        full_message = f"Storage error during {operation} operation on {storage_type}: {message}"
        
        context = context or {}
        context.update({
            'operation': operation,
            'storage_type': storage_type
        })
        
        super().__init__(full_message, context)


class SurveyNotFoundError(SurveyError):
    """Exception raised when a requested survey is not found."""
    
    def __init__(self, survey_id: str, context: Optional[dict] = None):
        """
        Initialize SurveyNotFoundError.
        
        Args:
            survey_id: ID of the survey that was not found
            context: Additional context information
        """
        self.survey_id = survey_id
        
        message = f"Survey not found: {survey_id}"
        
        context = context or {}
        context['survey_id'] = survey_id
        
        super().__init__(message, context)


class QuestionNotFoundError(SurveyError):
    """Exception raised when a requested question is not found."""
    
    def __init__(self, question_id: str, survey_id: Optional[str] = None, 
                 context: Optional[dict] = None):
        """
        Initialize QuestionNotFoundError.
        
        Args:
            question_id: ID of the question that was not found
            survey_id: ID of the survey containing the question
            context: Additional context information
        """
        self.question_id = question_id
        self.survey_id = survey_id
        
        message = f"Question not found: {question_id}"
        if survey_id:
            message += f" in survey {survey_id}"
        
        context = context or {}
        context['question_id'] = question_id
        if survey_id:
            context['survey_id'] = survey_id
        
        super().__init__(message, context)


class RateLimitError(APIError):
    """Exception raised when API rate limits are exceeded."""
    
    def __init__(self, service: str, retry_after: Optional[int] = None, 
                 context: Optional[dict] = None):
        """
        Initialize RateLimitError.
        
        Args:
            service: Name of the service that rate limited the request
            retry_after: Seconds to wait before retrying
            context: Additional context information
        """
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        
        super().__init__(
            service=service,
            message=message,
            status_code=429,
            retry_after=retry_after,
            context=context
        )