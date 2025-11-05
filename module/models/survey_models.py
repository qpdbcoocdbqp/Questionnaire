"""
Survey-related data models for the Survey AI Agent.

This module contains the core data structures for surveys, questions, answers,
and responses with validation and serialization capabilities.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


class QuestionType(Enum):
    """Enumeration of supported question types."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_TEXT = "open_text"
    RATING_SCALE = "rating_scale"


@dataclass
class Question:
    """Represents a survey question with validation rules."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    type: QuestionType = QuestionType.OPEN_TEXT
    options: Optional[List[str]] = None
    required: bool = True
    validation_rules: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate question data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate question data and raise ValidationError if invalid."""
        if not self.text.strip():
            raise ValueError("Question text cannot be empty")
        
        if self.type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
            if not self.options or len(self.options) < 2:
                raise ValueError(f"{self.type.value} questions must have at least 2 options")
        
        if self.type == QuestionType.RATING_SCALE:
            if not self.validation_rules or 'min_value' not in self.validation_rules or 'max_value' not in self.validation_rules:
                raise ValueError("Rating scale questions must have min_value and max_value in validation_rules")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary for serialization."""
        data = asdict(self)
        data['type'] = self.type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """Create Question instance from dictionary."""
        if 'type' in data:
            data['type'] = QuestionType(data['type'])
        return cls(**data)


@dataclass
class Answer:
    """Represents an answer to a survey question."""
    
    question_id: str
    value: Union[str, List[str], int, float]


    def __post_init__(self):
        """Validate answer data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate answer data."""
        if not self.question_id:
            raise ValueError("Answer must have a question_id")
        
        if self.value is None or (isinstance(self.value, str) and not self.value.strip()):
            raise ValueError("Answer value cannot be empty")
        
    def validate_against_question(self, question: Question) -> None:
        """Validate answer against its corresponding question."""
        if question.type == QuestionType.SINGLE_CHOICE:
            if not isinstance(self.value, str) or self.value not in question.options:
                raise ValueError(f"Single choice answer must be one of: {question.options}")
        
        elif question.type == QuestionType.MULTIPLE_CHOICE:
            if not isinstance(self.value, list):
                self.value = [self.value]
            for choice in self.value:
                if choice not in question.options:
                    raise ValueError(f"Multiple choice answer contains invalid option: {choice}")
        
        elif question.type == QuestionType.RATING_SCALE:
            if not isinstance(self.value, (int, float)):
                raise ValueError("Rating scale answer must be a number")
            
            rules = question.validation_rules or {}
            min_val = rules.get('min_value', 1)
            max_val = rules.get('max_value', 5)
            
            if not min_val <= self.value <= max_val:
                raise ValueError(f"Rating must be between {min_val} and {max_val}")
        
        elif question.type == QuestionType.OPEN_TEXT:
            if not isinstance(self.value, str):
                raise ValueError("Open text answer must be a string")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert answer to dictionary for serialization."""
        data = asdict(self)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Answer':
        """Create Answer instance from dictionary."""
        return cls(**data)


@dataclass
class Survey:
    """Represents a complete survey with questions."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    questions: List[Question] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    target_audience: str = ""
    
    def __post_init__(self):
        """Validate survey data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate survey data."""
        if not self.title.strip():
            raise ValueError("Survey title cannot be empty")
        
        if not self.questions:
            raise ValueError("Survey must have at least one question")
        
        # Validate all questions
        for question in self.questions:
            question.validate()
        
        # Check for duplicate question IDs
        question_ids = [q.id for q in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Survey contains duplicate question IDs")
    
    def add_question(self, question: Question) -> None:
        """Add a question to the survey."""
        question.validate()
        
        # Check for duplicate ID
        if any(q.id == question.id for q in self.questions):
            raise ValueError(f"Question with ID {question.id} already exists")
        
        self.questions.append(question)
    
    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get a question by its ID."""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert survey to dictionary for serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['questions'] = [q.to_dict() for q in self.questions]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Survey':
        """Create Survey instance from dictionary."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'questions' in data:
            data['questions'] = [Question.from_dict(q) for q in data['questions']]
        
        return cls(**data)


@dataclass
class SurveyResponse:
    """Represents a complete response to a survey."""
    
    survey_id: str
    user_id: str
    answers: List[Answer] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    
    def __post_init__(self):
        """Validate survey response data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate survey response data."""
        if not self.survey_id:
            raise ValueError("Survey response must have a survey_id")
        
        if not self.user_id:
            raise ValueError("Survey response must have a user_id")
        
        # Validate all answers
        for answer in self.answers:
            answer.validate()
        
        # Check for duplicate question answers
        question_ids = [a.question_id for a in self.answers]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Survey response contains duplicate answers for the same question")
    
    def add_answer(self, answer: Answer) -> None:
        """Add an answer to the response."""
        answer.validate()
        
        # Check for duplicate question answer
        if any(a.question_id == answer.question_id for a in self.answers):
            raise ValueError(f"Answer for question {answer.question_id} already exists")
        
        self.answers.append(answer)
    
    def get_answer_by_question_id(self, question_id: str) -> Optional[Answer]:
        """Get an answer by question ID."""
        for answer in self.answers:
            if answer.question_id == question_id:
                return answer
        return None
    
    def is_complete(self, survey: Survey) -> bool:
        """Check if response is complete based on required questions."""
        required_question_ids = {q.id for q in survey.questions if q.required}
        answered_question_ids = {a.question_id for a in self.answers}
        return required_question_ids.issubset(answered_question_ids)
    
    def mark_completed(self) -> None:
        """Mark the response as completed."""
        if self.completed_at is None:
            self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert survey response to dictionary for serialization."""
        data = asdict(self)
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        data['answers'] = [a.to_dict() for a in self.answers]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SurveyResponse':
        """Create SurveyResponse instance from dictionary."""
        if 'completed_at' in data and data['completed_at'] and isinstance(data['completed_at'], str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        if 'answers' in data:
            data['answers'] = [Answer.from_dict(a) for a in data['answers']]
        
        return cls(**data)