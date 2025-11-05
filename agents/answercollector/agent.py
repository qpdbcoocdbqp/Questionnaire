"""
Answer Collector Agent for Google ADK

This module implements a multi-agent system using LoopAgent and SequentialAgent patterns.
It combines iterative conversation collection with sequential database upload workflow.

"""

import logging
import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from uuid import uuid4


# ADK imports
from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext  
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

# Local imports
import sys
from pathlib import Path

# Add parent directory to path to import project modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


from module.models.config_models import SheetsConfig
from module.models.survey_models import SurveyResponse, Answer
from module.services.local_survery_handle import get_survey_dir, load_survey_from_file
from module.services.sheet_writer import SheetWriter
from module.prompts import QUESTION_ASKER_INSTRUCTION, DATABASE_UPLOADER_INSTRUCTION

logger = logging.getLogger(__name__)

load_dotenv()


# Initialize survey and configuration
survey = load_survey_from_file(
    survey_id=os.getenv("LOCAL_SURVEY_ID"),
    survey_dir=get_survey_dir(os.getenv("LOCAL_SURVEY_DIRECTORY"))
)
survey_details = f"問卷標題: {survey.title}\n問卷描述: {survey.description}\n\n"
questions_list = []
for i, q in enumerate(survey.questions):
    question_text = f"第 {i+1} 題: {q.text} (題型: {q.type.value})"
    if q.options:
        options_text = " 選項: " + ", ".join(q.options)
        question_text += options_text
    questions_list.append(question_text)

questions_str = "\n".join(questions_list)

# Initialize Google Sheets writer
config = SheetsConfig.from_env()
sheet_writer = SheetWriter(config)
sheet_writer.authenticate()

# define Survey Completed Agent (Custom Agent)
class SurveyCompletedAgent(BaseAgent):
    """
    Custom agent for checking if the questionnaire is completed.

    Reads the collected answers from session.state and compares with the total number of questions in the survey.
    """
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Check if the questionnaire is completed and emit corresponding events.
        """
        # collect messages and count runs
        chat_messages = ctx.session.state.get("chat_messages", [])
        num_answers = len(chat_messages) // 2
        required_question_count = len(survey.questions)
        logger.info(f"檢查問卷完成狀態: 當前回答數 {num_answers}/{required_question_count}")
        
        # check survey is completed, 
        # TODO: this rule may be wrong
        is_completed = num_answers >= required_question_count

        if is_completed:
            logger.info("問卷已完成。")
            # ctx.session.state["questionnaire_completed"] = True
            ctx.session.state["completed_at"] = datetime.now().isoformat()
            
            # finish LoopAgent
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True)
            )
        else:
            # continue LoopAgent
            remaining = required_question_count - num_answers
            logger.info(f"問卷尚未完成，還有 {remaining} 個問題待回答")
            yield Event(
                author=self.name,
                content=f"問卷尚未完成，請繼續回答。",
                error_ = "Response blocked due to safety settings.",
            )

# define Question Asker (LlmAgent)

def user_message_callback(
    callback_context: CallbackContext
) -> None:
    # create historic message
    session_state = callback_context.session.state
    message_history = session_state.get("chat_messages", [])
    logger.warning(f"Callback session state: {session_state}")
    # get user message
    if callback_context.user_content:
        if len(message_history) % 2 == 1:
            user_text = callback_context.user_content.parts[0].text
            logger.warning(user_text)
            # put massage to message_history
            message_history = session_state.get("chat_messages", [])
            message_history.append({
                "timestamp": datetime.now().isoformat(),
                "role": "user",
                "message": user_text
            })
    # get agent/model message
    question_text = session_state.get("question", None)
    if question_text is not None:
        # put massage to message_history
        message_history.append({
            "timestamp": datetime.now().isoformat(),
            "role": "asker",
            "message": question_text
            })

    # save historic history to state
    callback_context.state["chat_messages"] = message_history
    return None

question_asker = LlmAgent(
    name="QuestionAsker",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction=QUESTION_ASKER_INSTRUCTION.format(survey_details=survey_details, questions_str=questions_str),
    output_key="question",
    after_agent_callback=user_message_callback
    )

# define Answers Collector Loop (LoopAgent)
answers_collector_loop = LoopAgent(
    max_iterations=10,
    name="AnswersCollector",
    sub_agents=[
        question_asker,
        SurveyCompletedAgent(name="SurveyFinisher")
        ]
    )

# define Survey Answers Handler (LlmAgent)
class SurveyAnswers(BaseModel):
    """
    Represents the extracted answers from the user's conversation.
    """
    answers: List[Answer] = Field(..., description="List of answers to the survey questions.")

def before_answers_tructure_callback(
    callback_context: CallbackContext  
) -> None:
    callback_context.state["survey"] =  survey
    return None

survey_answers_handler = LlmAgent(
    name="SurveyAnswersHandler",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction="從問卷的對話中, 提取問卷答案. 問卷:\n\n{survey}\n\n對話:\n\n{chat_messages}",
    output_schema=SurveyAnswers,
    output_key="answers",
    before_agent_callback=before_answers_tructure_callback
    )

# define Database Uploader (LlmAgent)

def save_to_storage_tool(answers: dict, session_id: str) -> str:
    """
    Save the collected survey answers.
    
    Args:
        answers: Collected answers
        session_id: Session ID
    
    Returns:
        Message indicating the result of the save operation
    """
    try:
        response_dir = get_survey_dir(os.getenv("LOCAL_RESPONSE_DIRECTORY"))
        response_dir.mkdir(exist_ok=True)
        file_path = response_dir / f"{session_id}.json"
        survey_id = os.getenv("LOCAL_SURVEY_ID")
        logger.warning(f"[save_to_storage_tool] static_answers : {answers}")
        # write to local file
        with open(file_path, "w", encoding='utf-8') as f:
            # f.write(json.dumps(answers, indent=2))
            json.dump(answers, f, ensure_ascii=False, indent=2)

        logger.info(f"問卷答案已成功儲存至 {file_path}")
    
        survey_response = SurveyResponse(
            survey_id=survey_id,
            user_id=str(uuid4()),
            id=session_id,
            answers=[
                Answer(
                    question_id=answer.get("question_id"),
                    value=answer.get("value"),
                ) for answer in answers.get("answers")
                ],
            completed_at=datetime.now(),
            duration_seconds=120,
        )
        logger.warning(f"[save_to_storage_tool] survey_response : True")
        # upload to google spreadsheet
        sheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        logger.warning(f"\nAttempting to write to spreadsheet: {sheet_id}")
        header_success = sheet_writer.write_header(sheet_id=sheet_id, survey=survey)
        logger.warning(f"\nHeader success: {header_success}")
        upload_success = sheet_writer.write_response(sheet_id=sheet_id, response=survey_response, survey=survey)
        if upload_success:
            logger.info(f"問卷答案已成功儲存至 https://docs.google.com/spreadsheets/d/{sheet_id}")
        return f"成功將問卷答案儲存到本地檔案: {file_path}"
    except Exception as e:
        logger.error(f"儲存到本地檔案失敗: {e}")
        return f"儲存失敗: {str(e)}"

def before_inspect_callback(callback_context: CallbackContext) -> None:
    session_state = callback_context.session.state
    callback_context.session.state["session_id"] = callback_context.session.id
    logger.warning(f"[DatabaseUploader Before] Callback session state: {session_state}")

def after_inspect_callback(callback_context: CallbackContext) -> None:
    session_state = callback_context.session.state
    logger.warning(f"[DatabaseUploader After] Callback session state: {session_state}")

database_uploader = LlmAgent(
    name="DatabaseUploader",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    instruction=DATABASE_UPLOADER_INSTRUCTION,
    tools=[save_to_storage_tool],
    before_agent_callback=before_inspect_callback,
    # after_agent_callback=after_inspect_callback,
    )

# define root agent (SequentialAgent)
root_agent = SequentialAgent(
    name="AnswersCollectorWorkflow",
    sub_agents=[
        answers_collector_loop,   # Stage 1: Continuous conversation until the questionnaire is completed
        survey_answers_handler,   # Stage 2: Format answers after completion
        database_uploader         # Stage 3: Upload to database after completion
    ]
)

# ============================================================================
# Workflow Description
# ============================================================================

"""
1. Start the root_agent (AnswersCollectorWorkflow).
2. The AnswersCollector starts execution.
3. In the AnswersCollector loop:
   - QuestionAsker interacts with the user, collects answers, and updates the state (`chat_messages`).
   - SurveyCompletedAgent checks if the survey is complete.
4. When SurveyCompletedAgent emits `escalate=True`, the AnswersCollector loop terminates.
5. SurveyAnswersHandler starts execution, reads the state (`chat_messages`), and converts it into a structured SurveyAnswers output.
6. DatabaseUploader starts execution, reads the answers from the state (`answers`), and uses a tool to save the results.
7. The entire workflow is complete.
"""
