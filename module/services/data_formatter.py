"""
Data formatting utilities for Google Sheets integration.

This module provides structured data formatting, validation, and integrity
checking for survey responses before writing to spreadsheets.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import re

from module.models.survey_models import Survey, SurveyResponse, Answer, Question, QuestionType
from module.models.exceptions import ValidationError, DataStorageError


logger = logging.getLogger(__name__)


class SurveyDataFormatter:
    """
    Formats survey data for Google Sheets with proper validation and integrity checks.
    """
    
    # Column definitions for structured data format
    BASE_COLUMNS = [
        "用戶ID",        # User ID
        "問卷ID",        # Survey ID
        "回應ID",        # Response ID
        "完成時間",      # Completion timestamp
        "持續時間(秒)",  # Duration in seconds
        "完成狀態"       # Completion status
    ]
    
    def __init__(self):
        """Initialize the data formatter."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_headers(self, survey: Survey) -> List[str]:
        """
        Generate column headers for a survey spreadsheet.
        
        Args:
            survey: Survey object containing questions
            
        Returns:
            List[str]: Column headers in proper order
            
        Raises:
            ValidationError: If survey is invalid
        """
        if not survey or not survey.questions:
            raise ValidationError(
                "survey", survey, "Survey must have at least one question"
            )
        
        headers = self.BASE_COLUMNS.copy()
        
        # Add question headers with proper formatting
        for i, question in enumerate(survey.questions, 1):
            # Clean question text for header
            clean_text = self._clean_text_for_header(question.text)
            header = f"Q{i}: {clean_text}"
            
            # Add question type indicator
            type_indicator = self._get_type_indicator(question.type)
            if type_indicator:
                header += f" ({type_indicator})"
            
            headers.append(header)
            
            # Add confidence score column if applicable
            if self._should_include_confidence(question):
                headers.append(f"Q{i}_信心度")
        
        self.logger.debug(f"Generated {len(headers)} headers for survey {survey.id}")
        return headers
    
    def format_response_row(self, response: SurveyResponse, survey: Survey) -> List[str]:
        """
        Format a survey response into a spreadsheet row.
        
        Args:
            response: SurveyResponse object to format
            survey: Survey object for question mapping
            
        Returns:
            List[str]: Formatted row data
            
        Raises:
            ValidationError: If response data is invalid
            DataStorageError: If formatting fails
        """
        try:
            # Validate inputs
            self._validate_response_for_formatting(response, survey)
            
            # Start with base columns
            row_data = [
                str(response.user_id),                   # User ID
                str(response.survey_id),                 # Survey ID
                str(response.id),                        # Response ID
                self._format_timestamp(response.completed_at) if response.completed_at else "",
                str(response.duration_seconds),          # Duration
                self._get_completion_status(response, survey)  # Status
            ]
            
            # Add answer data for each question
            for question in survey.questions:
                answer = response.get_answer_by_question_id(question.id)
                
                if answer:
                    # Format the answer value
                    formatted_value = self._format_answer_value(answer, question)
                    row_data.append(formatted_value)
                    
                    # Add confidence score if applicable
                else:
                    # Empty answer
                    row_data.append("")
            
            self.logger.debug(f"Formatted response {response.id} into {len(row_data)} columns")
            return row_data
            
        except Exception as e:
            self.logger.error(f"Failed to format response {response.id}: {e}")
            if isinstance(e, ValidationError):
                raise
            raise DataStorageError(
                operation="format",
                message=f"Failed to format response: {str(e)}",
                storage_type="Google Sheets",
                context={
                    'response_id': response.id,
                    'survey_id': survey.id
                }
            )
    
    def validate_data_integrity(self, responses: List[SurveyResponse], 
                               survey: Survey) -> Dict[str, Any]:
        """
        Validate data integrity for a batch of responses.
        
        Args:
            responses: List of SurveyResponse objects to validate
            survey: Survey object for validation context
            
        Returns:
            Dict[str, Any]: Validation report with statistics and issues
        """
        report = {
            'total_responses': len(responses),
            'valid_responses': 0,
            'invalid_responses': 0,
            'issues': [],
            'statistics': {
                'completion_rate': 0.0,
                'average_duration': 0.0,
                'question_response_rates': {}
            }
        }
        
        valid_responses = []
        total_duration = 0
        completed_responses = 0
        
        # Question response tracking
        question_responses = {q.id: 0 for q in survey.questions}
        
        for response in responses:
            try:
                # Basic validation
                response.validate()
                
                # Check completeness
                is_complete = response.is_complete(survey)
                if is_complete:
                    completed_responses += 1
                
                # Track question responses
                for answer in response.answers:
                    if answer.question_id in question_responses:
                        question_responses[answer.question_id] += 1
                
                # Track duration
                total_duration += response.duration_seconds
                
                valid_responses.append(response)
                report['valid_responses'] += 1
                
            except Exception as e:
                report['invalid_responses'] += 1
                report['issues'].append({
                    'response_id': response.id,
                    'user_id': response.user_id,
                    'error': str(e),
                    'type': 'validation_error'
                })
        
        # Calculate statistics
        if valid_responses:
            report['statistics']['completion_rate'] = completed_responses / len(valid_responses)
            report['statistics']['average_duration'] = total_duration / len(valid_responses)
            
            # Question response rates
            for question in survey.questions:
                rate = question_responses[question.id] / len(valid_responses)
                report['statistics']['question_response_rates'][question.id] = rate
        
        self.logger.info(f"Data integrity check: {report['valid_responses']} valid, "
                        f"{report['invalid_responses']} invalid responses")
        
        return report
    
    def _validate_response_for_formatting(self, response: SurveyResponse, survey: Survey) -> None:
        """Validate response data before formatting."""
        if not response:
            raise ValidationError("response", response, "Response cannot be None")
        
        if not survey:
            raise ValidationError("survey", survey, "Survey cannot be None")
        
        if response.survey_id != survey.id:
            raise ValidationError(
                "survey_id", response.survey_id,
                f"Response survey_id {response.survey_id} does not match survey id {survey.id}"
            )
        
        # Validate answers against questions
        for answer in response.answers:
            question = survey.get_question_by_id(answer.question_id)
            if not question:
                raise ValidationError(
                    "question_id", answer.question_id,
                    f"Answer references non-existent question: {answer.question_id}"
                )
            
            # Validate answer against question
            try:
                answer.validate_against_question(question)
            except ValueError as e:
                raise ValidationError(
                    "answer_value", answer.value,
                    f"Invalid answer for question {question.id}: {str(e)}"
                )
    
    def _format_answer_value(self, answer: Answer, question: Question) -> str:
        """Format an answer value for spreadsheet display."""
        if answer.value is None:
            return ""
        
        if question.type == QuestionType.MULTIPLE_CHOICE:
            if isinstance(answer.value, list):
                return "; ".join(str(v) for v in answer.value)
            else:
                return str(answer.value)
        
        elif question.type == QuestionType.RATING_SCALE:
            if isinstance(answer.value, (int, float)):
                return str(answer.value)
            else:
                return str(answer.value)
        
        elif question.type in [QuestionType.SINGLE_CHOICE, QuestionType.OPEN_TEXT]:
            return str(answer.value)
        
        else:
            return str(answer.value)
    
    def _format_timestamp(self, timestamp: Optional[datetime]) -> str:
        """Format timestamp for spreadsheet display."""
        if timestamp is None:
            return ""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def _clean_text_for_header(self, text: str) -> str:
        """Clean text for use in spreadsheet headers."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Limit length for readability
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."
        
        return cleaned
    
    def _get_type_indicator(self, question_type: QuestionType) -> str:
        """Get a short indicator for question type."""
        indicators = {
            QuestionType.SINGLE_CHOICE: "單選",
            QuestionType.MULTIPLE_CHOICE: "多選",
            QuestionType.OPEN_TEXT: "開放",
            QuestionType.RATING_SCALE: "評分"
        }
        return indicators.get(question_type, "")
    
    def _should_include_confidence(self, question: Question) -> bool:
        """Determine if confidence score column should be included."""
        # Include confidence for open text questions where AI might be less certain
        return question.type == QuestionType.OPEN_TEXT
    
    def _get_completion_status(self, response: SurveyResponse, survey: Survey) -> str:
        """Get completion status string."""
        if response.completed_at:
            if response.is_complete(survey):
                return "完成"  # Complete
            else:
                return "部分完成"  # Partially complete
        else:
            return "進行中"  # In progress


class DataIntegrityChecker:
    """
    Performs data integrity checks and validation for survey responses.
    """
    
    def __init__(self):
        """Initialize the integrity checker."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def check_response_completeness(self, response: SurveyResponse, 
                                  survey: Survey) -> Dict[str, Any]:
        """
        Check completeness of a survey response.
        
        Args:
            response: SurveyResponse to check
            survey: Survey for validation context
            
        Returns:
            Dict[str, Any]: Completeness report
        """
        required_questions = [q for q in survey.questions if q.required]
        answered_question_ids = {a.question_id for a in response.answers}
        required_question_ids = {q.id for q in required_questions}
        
        missing_required = required_question_ids - answered_question_ids
        extra_answers = answered_question_ids - {q.id for q in survey.questions}
        
        return {
            'is_complete': len(missing_required) == 0,
            'total_questions': len(survey.questions),
            'required_questions': len(required_questions),
            'answered_questions': len(response.answers),
            'missing_required': list(missing_required),
            'extra_answers': list(extra_answers),
            'completion_percentage': len(answered_question_ids) / len(survey.questions) * 100
        }
    
    def validate_answer_consistency(self, responses: List[SurveyResponse], 
                                  survey: Survey) -> Dict[str, Any]:
        """
        Validate consistency across multiple responses.
        
        Args:
            responses: List of responses to validate
            survey: Survey for validation context
            
        Returns:
            Dict[str, Any]: Consistency validation report
        """
        issues = []
        statistics = {}
        
        # Check for duplicate responses from same user
        user_responses = {}
        for response in responses:
            if response.user_id in user_responses:
                issues.append({
                    'type': 'duplicate_user',
                    'user_id': response.user_id,
                    'response_ids': [user_responses[response.user_id], response.id]
                })
            else:
                user_responses[response.user_id] = response.id
        
        # Check answer value distributions for choice questions
        for question in survey.questions:
            if question.type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
                values = []
                for response in responses:
                    answer = response.get_answer_by_question_id(question.id)
                    if answer:
                        if isinstance(answer.value, list):
                            values.extend(answer.value)
                        else:
                            values.append(answer.value)
                
                # Check for invalid options
                if question.options:
                    invalid_values = [v for v in values if v not in question.options]
                    if invalid_values:
                        issues.append({
                            'type': 'invalid_option_values',
                            'question_id': question.id,
                            'invalid_values': list(set(invalid_values))
                        })
                
                # Store distribution statistics
                from collections import Counter
                statistics[question.id] = dict(Counter(values))
        
        return {
            'issues': issues,
            'statistics': statistics,
            'total_responses_checked': len(responses)
        }