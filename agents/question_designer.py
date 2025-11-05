"""
Question Designer module for generating survey questions using Gemini API.

This module provides functionality to generate contextual survey questions
based on topics and target audiences using Google's Gemini AI.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from module.models.survey_models import Question, QuestionType, Survey
from module.models.config_models import GeminiConfig
from module.models.exceptions import APIError, ValidationError
from .survey_templates import SurveyTemplate, TemplateManager


logger = logging.getLogger(__name__)


@dataclass
class QuestionGenerationRequest:
    """Request parameters for question generation."""
    topic: str
    target_audience: str
    question_count: int = 3
    question_types: Optional[List[QuestionType]] = None
    context: Optional[str] = None
    language: str = "zh-TW"


class QuestionDesigner:
    """
    Question Designer for generating survey questions using Gemini API.
    
    This class handles the generation of contextual survey questions based on
    topics, target audiences, and predefined templates.
    """
    
    def __init__(self, config: GeminiConfig, template_manager: Optional[TemplateManager] = None):
        """
        Initialize Question Designer with Gemini configuration.
        
        Args:
            config: Gemini API configuration
            template_manager: Template manager for predefined surveys
        """
        self.config = config
        self.template_manager = template_manager or TemplateManager()
        self._client: Optional[genai.GenerativeModel] = None
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Setup Gemini API client with configuration."""
        try:
            genai.configure(api_key=self.config.api_key)
            
            # Configure safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                response_mime_type="application/json"
            )
            
            self._client = genai.GenerativeModel(
                model_name=self.config.model_name,
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            
            logger.info(f"Gemini client initialized with model: {self.config.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup Gemini client: {e}")
            raise APIError("gemini", f"Failed to initialize Gemini API: {e}")
    
    async def generate_questions(
        self, 
        topic: str, 
        target_audience: str,
        question_count: int = 3,
        question_types: Optional[List[QuestionType]] = None,
        context: Optional[str] = None
    ) -> List[Question]:
        """
        Generate survey questions based on topic and target audience.
        
        Args:
            topic: Survey topic or theme
            target_audience: Target audience description
            question_count: Number of questions to generate
            question_types: Preferred question types (optional)
            context: Additional context for question generation
            
        Returns:
            List of generated Question objects
            
        Raises:
            APIError: If Gemini API call fails
            ValidationError: If generated questions are invalid
        """
        if not self._client:
            raise APIError("gemini", "Gemini client not initialized")
        
        request = QuestionGenerationRequest(
            topic=topic,
            target_audience=target_audience,
            question_count=question_count,
            question_types=question_types or [
                QuestionType.SINGLE_CHOICE,
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.OPEN_TEXT,
                QuestionType.RATING_SCALE
            ],
            context=context
        )
        
        try:
            prompt = self._build_generation_prompt(request)
            logger.info(f"Generating {question_count} questions for topic: {topic}")
            
            response = await asyncio.to_thread(
                self._client.generate_content, prompt
            )
            
            if not response.text:
                raise APIError("gemini", "Empty response from Gemini API")
            
            questions_data = json.loads(response.text)
            questions = self._parse_generated_questions(questions_data)
            
            # Validate question flow
            if not self.validate_question_flow(questions):
                logger.warning("Generated questions failed flow validation")
            
            logger.info(f"Successfully generated {len(questions)} questions")
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise APIError("gemini", f"Invalid JSON response from Gemini: {e}")
        
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            raise APIError("gemini", f"Question generation failed: {e}")
    
    def _build_generation_prompt(self, request: QuestionGenerationRequest) -> str:
        """
        Build prompt for Gemini API to generate questions.
        
        Args:
            request: Question generation request parameters
            
        Returns:
            Formatted prompt string
        """
        question_types_str = ", ".join([qt.value for qt in request.question_types])
        
        prompt = f"""
你是一個專業的問卷設計專家。請根據以下要求生成問卷題目：

主題: {request.topic}
目標受眾: {request.target_audience}
題目數量: {request.question_count}
支援的題型: {question_types_str}

{f"額外背景資訊: {request.context}" if request.context else ""}

請生成一份結構化的問卷，包含不同類型的問題。每個問題都應該：
1. 與主題高度相關
2. 適合目標受眾
3. 清晰易懂
4. 有助於收集有價值的資料

請以JSON格式回應，結構如下：
{{
    "questions": [
        {{
            "text": "問題內容",
            "type": "single_choice|multiple_choice|open_text|rating_scale",
            "options": ["選項1", "選項2"] (僅適用於選擇題),
            "required": true|false,
            "validation_rules": {{
                "min_value": 1,
                "max_value": 5
            }} (僅適用於評分題)
        }}
    ]
}}

確保問題類型分佈合理，包含：
- 基本資訊收集問題
- 態度和滿意度評估
- 開放式意見收集
- 量化評分問題

請確保所有問題都是繁體中文，並且適合台灣地區的使用者。
"""
        return prompt
    
    def _parse_generated_questions(self, questions_data: Dict[str, Any]) -> List[Question]:
        """
        Parse generated questions from Gemini response.
        
        Args:
            questions_data: Raw questions data from Gemini
            
        Returns:
            List of Question objects
            
        Raises:
            ValidationError: If question data is invalid
        """
        if "questions" not in questions_data:
            raise ValidationError("questions", questions_data, "Missing 'questions' field in response")
        
        questions = []
        
        for i, q_data in enumerate(questions_data["questions"]):
            try:
                # Parse question type
                question_type = QuestionType(q_data.get("type", "open_text"))
                
                # Create question object
                question = Question(
                    text=q_data.get("text", "").strip(),
                    type=question_type,
                    options=q_data.get("options"),
                    required=q_data.get("required", True),
                    validation_rules=q_data.get("validation_rules")
                )
                
                # Validate question
                question.validate()
                questions.append(question)
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid question {i}: {e}")
                continue
        
        if not questions:
            raise ValidationError("questions", questions_data, "No valid questions generated")
        
        return questions
    
    def validate_question_flow(self, questions: List[Question]) -> bool:
        """
        Validate the logical flow and distribution of questions.
        
        Args:
            questions: List of questions to validate
            
        Returns:
            True if question flow is valid, False otherwise
        """
        if not questions:
            return False
        
        # Check question type distribution
        type_counts = {}
        for question in questions:
            type_counts[question.type] = type_counts.get(question.type, 0) + 1
        
        # Ensure we have a reasonable distribution
        total_questions = len(questions)
        
        # At least one open text question for feedback
        if type_counts.get(QuestionType.OPEN_TEXT, 0) == 0:
            logger.warning("No open text questions found")
            return False
        
        # Not too many open text questions (should be < 50%)
        if type_counts.get(QuestionType.OPEN_TEXT, 0) > total_questions * 0.5:
            logger.warning("Too many open text questions")
            return False
        
        # Check for required questions
        required_count = sum(1 for q in questions if q.required)
        if required_count == 0:
            logger.warning("No required questions found")
            return False
        
        # Validate individual questions
        for question in questions:
            try:
                question.validate()
            except ValueError as e:
                logger.warning(f"Question validation failed: {e}")
                return False
        
        return True
    
    async def load_template(self, template_name: str) -> SurveyTemplate:
        """
        Load a predefined survey template.
        
        Args:
            template_name: Name of the template to load
            
        Returns:
            SurveyTemplate object
            
        Raises:
            ValidationError: If template not found or invalid
        """
        try:
            template = self.template_manager.get_template(template_name)
            logger.info(f"Loaded template: {template_name}")
            return template
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            raise ValidationError("template_name", template_name, str(e))
    
    def create_survey_from_questions(
        self, 
        questions: List[Question], 
        title: str, 
        description: str = "",
        target_audience: str = ""
    ) -> Survey:
        """
        Create a Survey object from generated questions.
        
        Args:
            questions: List of questions
            title: Survey title
            description: Survey description
            target_audience: Target audience description
            
        Returns:
            Survey object
            
        Raises:
            ValidationError: If survey data is invalid
        """
        try:
            survey = Survey(
                title=title,
                description=description,
                questions=questions,
                target_audience=target_audience
            )
            
            survey.validate()
            return survey
            
        except ValueError as e:
            raise ValidationError("survey", {"title": title, "questions": len(questions)}, str(e))
    
    async def generate_survey(
        self,
        topic: str,
        target_audience: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        question_count: int = 3,
        question_types: Optional[List[QuestionType]] = None,
        context: Optional[str] = None
    ) -> Survey:
        """
        Generate a complete survey with questions.
        
        Args:
            topic: Survey topic
            target_audience: Target audience
            title: Survey title (auto-generated if not provided)
            description: Survey description (auto-generated if not provided)
            question_count: Number of questions to generate
            question_types: Preferred question types
            context: Additional context
            
        Returns:
            Complete Survey object
        """
        # Generate questions
        questions = await self.generate_questions(
            topic=topic,
            target_audience=target_audience,
            question_count=question_count,
            question_types=question_types,
            context=context
        )
        
        # Auto-generate title and description if not provided
        if not title:
            title = f"{topic} 問卷調查"
        
        if not description:
            description = f"針對 {target_audience} 進行的 {topic} 相關問卷調查"
        
        # Create and return survey
        return self.create_survey_from_questions(
            questions=questions,
            title=title,
            description=description,
            target_audience=target_audience
        )
    
    def list_available_templates(self) -> List[str]:
        """
        List all available survey templates.
        
        Returns:
            List of template names
        """
        return self.template_manager.list_templates()
    
    def get_templates_by_category(self, category: str) -> List[SurveyTemplate]:
        """
        Get templates by category.
        
        Args:
            category: Template category
            
        Returns:
            List of templates in the category
        """
        return self.template_manager.get_templates_by_category(category)
    
    async def create_survey_from_template(
        self, 
        template_name: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Survey:
        """
        Create a survey from a template with optional customizations.
        
        Args:
            template_name: Name of the template to use
            customizations: Optional customizations to apply
            
        Returns:
            Survey object created from template
            
        Raises:
            ValidationError: If template not found or customizations invalid
        """
        try:
            if customizations:
                # Apply customizations to template
                template = self.template_manager.customize_template(
                    template_name, customizations
                )
            else:
                # Use template as-is
                template = await self.load_template(template_name)
            
            # Convert template to survey
            survey = template.to_survey()
            
            logger.info(f"Created survey from template: {template_name}")
            return survey
            
        except Exception as e:
            logger.error(f"Failed to create survey from template {template_name}: {e}")
            raise ValidationError("template_creation", template_name, str(e))
    
    async def enhance_template_with_ai(
        self,
        template_name: str,
        enhancement_request: str,
        target_audience: Optional[str] = None
    ) -> Survey:
        """
        Enhance an existing template with AI-generated additional questions.
        
        Args:
            template_name: Name of the base template
            enhancement_request: Description of what to enhance
            target_audience: Optional target audience override
            
        Returns:
            Enhanced survey with additional AI-generated questions
        """
        try:
            # Load base template
            template = await self.load_template(template_name)
            base_survey = template.to_survey()
            
            # Generate additional questions based on enhancement request
            additional_questions = await self.generate_questions(
                topic=enhancement_request,
                target_audience=target_audience or template.target_audience,
                question_count=3,  # Add a few additional questions
                context=f"這是基於 '{template.title}' 模板的增強版問卷"
            )
            
            # Combine base questions with additional questions
            enhanced_questions = base_survey.questions + additional_questions
            
            # Create enhanced survey
            enhanced_survey = Survey(
                title=f"{base_survey.title} (增強版)",
                description=f"{base_survey.description}\n\n增強內容：{enhancement_request}",
                questions=enhanced_questions,
                target_audience=target_audience or base_survey.target_audience
            )
            
            logger.info(f"Enhanced template {template_name} with {len(additional_questions)} additional questions")
            return enhanced_survey
            
        except Exception as e:
            logger.error(f"Failed to enhance template {template_name}: {e}")
            raise ValidationError("template_enhancement", template_name, str(e))