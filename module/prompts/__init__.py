"""
Prompts package for Survey AI Agent.

This package contains all text prompts used by the agent.
"""

from .agent_instruction import AGENT_INSTRUCTION, QUESTION_ASKER_INSTRUCTION, DATABASE_UPLOADER_INSTRUCTION
from .response_templates import (
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

__all__ = [
    'AGENT_INSTRUCTION',
    "QUESTION_ASKER_INSTRUCTION",
    "DATABASE_UPLOADER_INSTRUCTION",
    'success_create_from_template',
    'error_create_from_template',
    'list_templates_header',
    'list_templates_item',
    'list_templates_footer',
    'no_templates_available',
    'error_list_templates',
    'success_create_survey',
    'error_create_survey',
    "success_get_survey_by_id",
    "survey_not_found",
    "error_get_survey_by_id",
]

