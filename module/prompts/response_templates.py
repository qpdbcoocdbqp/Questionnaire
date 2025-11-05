"""
Response templates for survey agent tools.

This module contains response formatting templates for various survey operations.
"""

from typing import Dict, Any, List


def success_create_from_template(template_name: str, survey_title: str, survey_description: str, 
                                  target_audience: str, question_count: int, survey_id: str) -> str:
    """
    Template for successful survey creation from template.
    
    Args:
        template_name: Name of the template used
        survey_title: Title of the created survey
        survey_description: Description of the survey
        target_audience: Target audience
        question_count: Number of questions
        survey_id: Survey ID
        
    Returns:
        Formatted success message
    """
    return f"""成功從模板「{template_name}」創建問卷「{survey_title}」

問卷資訊：
- 描述：{survey_description}
- 目標受眾：{target_audience}
- 問題數量：{question_count} 題
- 問卷 ID：{survey_id}

問卷已準備就緒！"""


def error_create_from_template(error_message: str) -> str:
    """
    Template for failed survey creation from template.
    
    Args:
        error_message: Error message
        
    Returns:
        Formatted error message
    """
    return f"從模板創建問卷失敗：{error_message}\n\n提示：請先使用 list_templates 查看可用的模板名稱。"


def list_templates_header(template_count: int) -> str:
    """
    Template for list templates header.
    
    Args:
        template_count: Number of templates found
        
    Returns:
        Header text
    """
    return f"找到 {template_count} 個可用模板：\n\n"


def list_templates_item(index: int, title: str, name: str, description: str, 
                        question_count: int, category: str, target_audience: str) -> str:
    """
    Template for individual template in list.
    
    Args:
        index: Template index
        title: Template title
        name: Template name
        description: Template description
        question_count: Number of questions
        category: Template category
        target_audience: Target audience
        
    Returns:
        Formatted template item
    """
    return f"""{index}. **{title}** (名稱: {name})
   - 描述：{description}
   - 問題數：{question_count} 題
   - 類別：{category}
   - 目標受眾：{target_audience}
   
"""


def list_templates_footer() -> str:
    """
    Template for list templates footer.
    
    Returns:
        Footer text
    """
    return "\n使用 create_survey_from_template 並提供模板名稱來創建問卷。"


def no_templates_available() -> str:
    """
    Template when no templates are available.
    
    Returns:
        Message text
    """
    return "目前沒有可用的模板。"


def error_list_templates(error_message: str) -> str:
    """
    Template for failed template listing.
    
    Args:
        error_message: Error message
        
    Returns:
        Formatted error message
    """
    return f"列出模板失敗：{error_message}"


def success_create_survey(survey_title: str, survey_description: str, 
                          target_audience: str, question_count: int, 
                          survey_id: str, questions_summary: str) -> str:
    """
    Template for successful survey creation.
    
    Args:
        survey_title: Title of the created survey
        survey_description: Description of the survey
        target_audience: Target audience
        question_count: Number of questions
        survey_id: Survey ID
        questions_summary: Summary of questions (first 5 + remaining count)
        
    Returns:
        Formatted success message
    """
    return f"""成功創建問卷「{survey_title}」

問卷資訊：
- 描述：{survey_description}
- 目標受眾：{target_audience}
- 問題數量：{question_count} 題
- 問卷 ID：{survey_id}

問題預覽：
{questions_summary}

您可以開始使用這個問卷進行調查了！"""


def error_create_survey(error_message: str) -> str:
    """
    Template for failed survey creation.
    
    Args:
        error_message: Error message
        
    Returns:
        Formatted error message
    """
    return f"創建問卷失敗：{error_message}"


def success_get_survey_by_id(survey_id: str, survey_title: str, survey_description: str,
                             target_audience: str, created_at: str, question_count: int,
                             questions_detail: str) -> str:
    """
    Template for successful survey retrieval by ID.
    
    Args:
        survey_id: Survey ID
        survey_title: Title of the survey
        survey_description: Description of the survey
        target_audience: Target audience
        created_at: Creation time formatted string
        question_count: Number of questions
        questions_detail: Detailed list of questions
        
    Returns:
        Formatted success message
    """
    return f"""問卷讀取成功

問卷資訊：
  ID: {survey_id}
  標題: {survey_title}
  描述: {survey_description}
  目標受眾: {target_audience}
  創建時間: {created_at}
  問題數量: {question_count}

問題列表：
{questions_detail}
"""


def survey_not_found(survey_id: str) -> str:
    """
    Template for when survey is not found.
    
    Args:
        survey_id: Survey ID that was not found
        
    Returns:
        Formatted error message
    """
    return f"找不到問卷 ID: {survey_id}\n\n請確認問卷ID是否正確。您可以使用 create_survey 或 create_survey_from_template 創建新問卷。"


def error_get_survey_by_id(error_message: str) -> str:
    """
    Template for failed survey retrieval by ID.
    
    Args:
        error_message: Error message
        
    Returns:
        Formatted error message
    """
    return f"讀取問卷時發生錯誤：{error_message}"