"""
Survey templates module for predefined survey structures.

This module provides predefined survey templates including the e-commerce
satisfaction survey template and template management functionality.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from module.models.survey_models import Question, QuestionType, Survey
from module.models.exceptions import ValidationError, SurveyNotFoundError


logger = logging.getLogger(__name__)


@dataclass
class SurveyTemplate:
    """Template for predefined survey structures."""
    name: str
    title: str
    description: str
    questions: List[Question]
    target_audience: str
    category: str
    language: str = "zh-TW"
    
    def to_dict(self) -> Dict:
        """Convert template to dictionary."""
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'questions': [q.to_dict() for q in self.questions],
            'target_audience': self.target_audience,
            'category': self.category,
            'language': self.language
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SurveyTemplate':
        """Create template from dictionary."""
        questions = [Question.from_dict(q) for q in data.get('questions', [])]
        
        return cls(
            name=data['name'],
            title=data['title'],
            description=data['description'],
            questions=questions,
            target_audience=data['target_audience'],
            category=data['category'],
            language=data.get('language', 'zh-TW')
        )
    
    def to_survey(self) -> Survey:
        """Convert template to Survey object."""
        return Survey(
            title=self.title,
            description=self.description,
            questions=self.questions.copy(),
            target_audience=self.target_audience
        )


class TemplateManager:
    """Manager for survey templates."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager.
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self._templates: Dict[str, SurveyTemplate] = {}
        self._load_builtin_templates()
    
    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        # Load e-commerce satisfaction survey template
        ecommerce_template = self._create_ecommerce_satisfaction_template()
        self._templates[ecommerce_template.name] = ecommerce_template
        
        logger.info(f"Loaded {len(self._templates)} built-in templates")
    
    def _create_ecommerce_satisfaction_template(self) -> SurveyTemplate:
        """Create the e-commerce satisfaction survey template."""
        questions = [
            # 基本資訊收集
            Question(
                text="請問您多久在線上購物一次？",
                type=QuestionType.SINGLE_CHOICE,
                options=[
                    "每天",
                    "每週2-3次",
                    "每週1次",
                    "每月2-3次",
                    "每月1次",
                    "很少購物"
                ],
                required=True
            ),
            
            Question(
                text="您主要購買哪些類別的商品？（可複選）",
                type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "服飾配件",
                    "3C電子產品",
                    "家居用品",
                    "美妝保養",
                    "食品飲料",
                    "書籍文具",
                    "運動用品",
                    "其他"
                ],
                required=True
            ),
            
            # 整體滿意度評估
            Question(
                text="整體而言，您對我們的線上購物體驗滿意度如何？",
                type=QuestionType.RATING_SCALE,
                required=True,
                validation_rules={
                    "min_value": 1,
                    "max_value": 5,
                    "scale_labels": {
                        1: "非常不滿意",
                        2: "不滿意", 
                        3: "普通",
                        4: "滿意",
                        5: "非常滿意"
                    }
                }
            ),
            
            Question(
                text="請評價我們網站的使用便利性",
                type=QuestionType.RATING_SCALE,
                required=True,
                validation_rules={
                    "min_value": 1,
                    "max_value": 5,
                    "scale_labels": {
                        1: "非常難用",
                        2: "難用",
                        3: "普通", 
                        4: "好用",
                        5: "非常好用"
                    }
                }
            ),
            
            # 各項服務滿意度
            Question(
                text="請評價我們的商品品質",
                type=QuestionType.RATING_SCALE,
                required=True,
                validation_rules={
                    "min_value": 1,
                    "max_value": 5,
                    "scale_labels": {
                        1: "非常差",
                        2: "差",
                        3: "普通",
                        4: "好", 
                        5: "非常好"
                    }
                }
            ),
            
            Question(
                text="請評價我們的配送服務",
                type=QuestionType.RATING_SCALE,
                required=True,
                validation_rules={
                    "min_value": 1,
                    "max_value": 5,
                    "scale_labels": {
                        1: "非常差",
                        2: "差",
                        3: "普通",
                        4: "好",
                        5: "非常好"
                    }
                }
            ),
            
            Question(
                text="請評價我們的客服服務",
                type=QuestionType.RATING_SCALE,
                required=False,
                validation_rules={
                    "min_value": 1,
                    "max_value": 5,
                    "scale_labels": {
                        1: "非常差",
                        2: "差", 
                        3: "普通",
                        4: "好",
                        5: "非常好"
                    }
                }
            ),
            
            Question(
                text="您認為我們的商品價格如何？",
                type=QuestionType.SINGLE_CHOICE,
                options=[
                    "非常便宜",
                    "便宜",
                    "合理",
                    "昂貴",
                    "非常昂貴"
                ],
                required=True
            ),
            
            # 開放式回饋
            Question(
                text="請分享您對我們服務的具體建議或改善意見",
                type=QuestionType.OPEN_TEXT,
                required=False
            ),
            
            Question(
                text="您最喜歡我們服務的哪個部分？",
                type=QuestionType.OPEN_TEXT,
                required=False
            ),
            
            # 後續互動
            Question(
                text="您會推薦朋友使用我們的服務嗎？",
                type=QuestionType.SINGLE_CHOICE,
                options=[
                    "絕對會推薦",
                    "可能會推薦",
                    "不確定",
                    "可能不會推薦",
                    "絕對不會推薦"
                ],
                required=True
            ),
            
            Question(
                text="如果您願意，請留下您的聯絡方式以便我們提供更好的服務（可選）",
                type=QuestionType.OPEN_TEXT,
                required=False
            )
        ]
        
        return SurveyTemplate(
            name="ecommerce_satisfaction",
            title="電商消費滿意度調查",
            description="針對線上購物體驗進行全面性的滿意度調查，包含商品品質、配送服務、客服體驗等各個面向的評估。",
            questions=questions,
            target_audience="線上購物消費者",
            category="customer_satisfaction",
            language="zh-TW"
        )
    
    def get_template(self, template_name: str) -> SurveyTemplate:
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            SurveyTemplate object
            
        Raises:
            SurveyNotFoundError: If template not found
        """
        if template_name not in self._templates:
            raise SurveyNotFoundError(
                template_name, 
                context={'available_templates': list(self._templates.keys())}
            )
        
        return self._templates[template_name]
    
    def list_templates(self) -> List[str]:
        """
        List all available template names.
        
        Returns:
            List of template names
        """
        return list(self._templates.keys())
    
    def get_templates_by_category(self, category: str) -> List[SurveyTemplate]:
        """
        Get templates by category.
        
        Args:
            category: Template category
            
        Returns:
            List of templates in the category
        """
        return [
            template for template in self._templates.values()
            if template.category == category
        ]
    
    def add_template(self, template: SurveyTemplate) -> None:
        """
        Add a new template.
        
        Args:
            template: Template to add
            
        Raises:
            ValidationError: If template is invalid
        """
        try:
            # Validate template by converting to survey
            survey = template.to_survey()
            survey.validate()
            
            self._templates[template.name] = template
            logger.info(f"Added template: {template.name}")
            
        except Exception as e:
            raise ValidationError(
                "template", 
                template.name, 
                f"Invalid template: {e}"
            )
    
    def save_template(self, template: SurveyTemplate, file_path: Optional[Path] = None) -> None:
        """
        Save template to file.
        
        Args:
            template: Template to save
            file_path: Path to save file (optional)
        """
        if file_path is None:
            self.templates_dir.mkdir(exist_ok=True)
            file_path = self.templates_dir / f"{template.name}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved template {template.name} to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save template {template.name}: {e}")
            raise
    
    def load_template_from_file(self, file_path: Path) -> SurveyTemplate:
        """
        Load template from file.
        
        Args:
            file_path: Path to template file
            
        Returns:
            SurveyTemplate object
            
        Raises:
            ValidationError: If template file is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            template = SurveyTemplate.from_dict(data)
            
            # Validate template
            survey = template.to_survey()
            survey.validate()
            
            logger.info(f"Loaded template {template.name} from {file_path}")
            return template
            
        except Exception as e:
            raise ValidationError(
                "template_file",
                str(file_path),
                f"Failed to load template: {e}"
            )
    
    def customize_template(
        self, 
        template_name: str, 
        customizations: Dict
    ) -> SurveyTemplate:
        """
        Customize an existing template.
        
        Args:
            template_name: Name of the base template
            customizations: Dictionary of customizations to apply
            
        Returns:
            Customized SurveyTemplate
            
        Raises:
            SurveyNotFoundError: If base template not found
            ValidationError: If customizations are invalid
        """
        base_template = self.get_template(template_name)
        
        # Create a copy of the template
        template_dict = base_template.to_dict()
        
        # Apply customizations
        if 'title' in customizations:
            template_dict['title'] = customizations['title']
        
        if 'description' in customizations:
            template_dict['description'] = customizations['description']
        
        if 'target_audience' in customizations:
            template_dict['target_audience'] = customizations['target_audience']
        
        if 'questions' in customizations:
            # Handle question customizations
            questions_custom = customizations['questions']
            
            if isinstance(questions_custom, list):
                # Replace all questions
                template_dict['questions'] = questions_custom
            elif isinstance(questions_custom, dict):
                # Modify specific questions by index
                for index, question_data in questions_custom.items():
                    if isinstance(index, str) and index.isdigit():
                        index = int(index)
                    
                    if 0 <= index < len(template_dict['questions']):
                        template_dict['questions'][index].update(question_data)
        
        # Create new template name
        custom_name = f"{template_name}_custom_{hash(str(customizations)) % 10000}"
        template_dict['name'] = custom_name
        
        try:
            customized_template = SurveyTemplate.from_dict(template_dict)
            
            # Validate customized template
            survey = customized_template.to_survey()
            survey.validate()
            
            return customized_template
            
        except Exception as e:
            raise ValidationError(
                "customizations",
                customizations,
                f"Invalid template customizations: {e}"
            )


# Global template manager instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """Get the global template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager


def get_ecommerce_satisfaction_template() -> SurveyTemplate:
    """Get the e-commerce satisfaction survey template."""
    return get_template_manager().get_template("ecommerce_satisfaction")


def list_available_templates() -> List[str]:
    """List all available template names."""
    return get_template_manager().list_templates()