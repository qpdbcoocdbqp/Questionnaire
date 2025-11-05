"""
Survey AI Agent for Google ADK

This module implements a survey agent that can be launched with ADK web interface.
It integrates existing survey functionality (question design, answer collection, 
data storage) as ADK tools.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# ADK imports
from google.adk.agents.llm_agent import LlmAgent

# Local imports
import sys
from pathlib import Path

# Add parent directory to path to import project modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.question_designer import QuestionDesigner
from agents.survey_templates import get_template_manager
from config.settings import get_config
from module.services.local_survery_handle import get_survey_dir, load_survey_from_file, save_survey_to_file
from module.prompts import (
    AGENT_INSTRUCTION,
    success_create_from_template,
    error_create_from_template,
    list_templates_header,
    list_templates_item,
    list_templates_footer,
    no_templates_available,
    error_list_templates,
    success_create_survey,
    error_create_survey,
    success_get_survey_by_id,
    survey_not_found,
    error_get_survey_by_id,
)


logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global state
SURVEY_DIR = get_survey_dir(storage_dir = os.getenv("LOCAL_SURVEY_DIRECTORY"))

def create_survey_tools_sync(question_designer: QuestionDesigner) -> List:
    """
    Create ADK tools from survey functionality.
    Tools are defined as async functions with type hints.
    
    Args:
        question_designer: Question Designer instance
        
    Returns:
        List of tool functions
    """
    tools = []
    
    # Tool: Create Survey
    async def create_survey(
        topic: str,
        target_audience: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        question_count: int = 3
    ) -> str:
        """
        Creates a new questionnaire based on the topic and target audience.
        Supports specifying the number of questions, title, and description.
        
        Args:
            topic: The theme or topic of the questionnaire, e.g., product satisfaction, customer experience, market research, etc.
            target_audience: Description of the target audience, e.g., general consumers, business customers, students, etc.
            title: The title of the questionnaire (optional, will be auto-generated if not provided).
            description: The description of the questionnaire (optional, will be auto-generated if not provided).
            question_count: The number of questions (default is 3, range 1-10).
        """
        try:
            survey = await question_designer.generate_survey(
                topic=topic,
                target_audience=target_audience,
                title=title,
                description=description,
                question_count=question_count
            )
            
            # Save survey to file
            save_survey_to_file(survey, survey_dir=SURVEY_DIR)
            
            # Format output for user
            questions_summary = "\n".join([
                f"{i+1}. {q.text} ({q.type.value})" 
                for i, q in enumerate(survey.questions[:5])
            ])
            if len(survey.questions) > 5:
                questions_summary += f"\n... 還有 {len(survey.questions) - 5} 個問題"
            return success_create_survey(
                survey_title=survey.title,
                survey_description=survey.description,
                target_audience=survey.target_audience,
                question_count=len(survey.questions),
                survey_id=survey.id,
                questions_summary=questions_summary
            )
        except Exception as e:
            logger.error(f"Failed to create survey: {e}")
            return error_create_survey(str(e))

    tools.append(create_survey)
    
    # Tool: Create Survey from Template
    async def create_survey_from_template(
        template_name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_audience: Optional[str] = None
    ) -> str:
        """
        Create a survey using a default template. You can select a template and customize it.
        
        Args:
            template_name: Template name, e.g., ecommerce_satisfaction
            title: Custom title (optional)
            description: Custom description (optional)
            target_audience: Custom target audience (optional)
        """
        try:
            customizations = {}
            if title:
                customizations["title"] = title
            if description:
                customizations["description"] = description
            if target_audience:
                customizations["target_audience"] = target_audience
            
            survey = await question_designer.create_survey_from_template(
                template_name=template_name,
                customizations=customizations if customizations else None
            )
            
            # Save survey to file
            save_survey_to_file(survey, survey_dir=SURVEY_DIR)

            return success_create_from_template(
                template_name=template_name,
                survey_title=survey.title,
                survey_description=survey.description,
                target_audience=survey.target_audience,
                question_count=len(survey.questions),
                survey_id=survey.id
            )
        except Exception as e:
            logger.error(f"Failed to create survey from template: {e}")
            return error_create_from_template(str(e))
    
    tools.append(create_survey_from_template)
    
    # Tool: List Templates
    async def list_templates() -> str:
        """
        list all survay templates 
        """
        try:
            templates = question_designer.list_available_templates()
            template_manager = get_template_manager()
            
            template_details = []
            for template_name in templates:
                try:
                    template = template_manager.get_template(template_name)
                    template_details.append({
                        "name": template.name,
                        "title": template.title,
                        "description": template.description,
                        "question_count": len(template.questions),
                        "category": template.category,
                        "target_audience": template.target_audience
                    })
                except Exception as e:
                    logger.warning(f"Failed to get template details for {template_name}: {e}")
            
            if not template_details:
                return no_templates_available()
            
            result = list_templates_header(len(template_details))
            for i, tmpl in enumerate(template_details, 1):
                result += list_templates_item(
                    index=i,
                    title=tmpl['title'],
                    name=tmpl['name'],
                    description=tmpl['description'],
                    question_count=tmpl['question_count'],
                    category=tmpl['category'],
                    target_audience=tmpl['target_audience']
                )
            
            result += list_templates_footer()
            return result
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return error_list_templates(str(e))
    
    tools.append(list_templates)
    
    # Tool: Get Survey by ID
    async def get_survey_by_id(survey_id: str) -> str:
        """
        Load a survey from local file by survey ID.
        
        Args:
            survey_id: Survey ID
        """
        try:
            survey = load_survey_from_file(survey_id, survey_dir=SURVEY_DIR)
            if survey is None:
                return survey_not_found(survey_id)

            # Format questions detail
            questions_detail = "\n".join([
                f"  {i+1}. {q.text} ({q.type.value})"
                for i, q in enumerate(survey.questions)
            ])
            # Format creation time
            created_at_str = survey.created_at.strftime('%Y-%m-%d %H:%M:%S')
            return success_get_survey_by_id(
                    survey_id=survey.id,
                    survey_title=survey.title,
                    survey_description=survey.description,
                    target_audience=survey.target_audience,
                    created_at=created_at_str,
                    question_count=len(survey.questions),
                    questions_detail=questions_detail
                )
        except Exception as e:
            logger.error(f"Failed to get survey by ID: {e}")
            return error_get_survey_by_id(str(e))
    tools.append(get_survey_by_id)
    
    return tools

# ADK web expects `root_agent` to be available in the module
# It should be either:
# 1. A direct agent instance
# 2. An async function that returns an agent (which ADK will await)

def get_tools():
    """
    Creates an ADK Agent equipped with survey tools.
    
    Returns:
        Tuple of (root_agent, exit_stack) for cleanup
    """
    # Initialize configuration
    config = get_config()
    
    # Initialize Question Designer
    question_designer = QuestionDesigner(config.gemini)
    logger.info("Question Designer initialized")
    
    # Create tools from existing survey functionality
    tools = create_survey_tools_sync(
        question_designer=question_designer,
    )
    
    logger.info(f"Created {len(tools)} survey tools")
    return tools

# main
tools = get_tools()

root_agent = LlmAgent(
    model=os.getenv("GEMINI_MODEL"),
    name="survey_assistant",
    instruction=AGENT_INSTRUCTION,
    tools=tools,
    )
