from module.models.survey_models import (
    Survey,
    SurveyResponse,
    Answer,
    Question,
    QuestionType,
)
from uuid import uuid4
import datetime

# --- 1. Create a sample Survey ---
mock_survey = Survey(
        id="test-survey-001",
        title="Sample Survey for Testing",
        description="This is a test survey to demonstrate writing to Google Sheets.",
        questions=[
            Question(
                id="q1",
                text="What is your favorite color?",
                type=QuestionType.SINGLE_CHOICE,
                options=["Red", "Green", "Blue"],
                required=True,
            ),
            Question(
                id="q2",
                text="Which fruits do you like? (Select all that apply)",
                type=QuestionType.MULTIPLE_CHOICE,
                options=["Apple", "Banana", "Orange", "Grape"],
                required=True,
            ),
            Question(id="q3", text="Any feedback for us?", type=QuestionType.OPEN_TEXT, required=False),
            Question(
                id="q4",
                text="How would you rate our service? (1-5)",
                type=QuestionType.RATING_SCALE,
                validation_rules={"min_value": 1, "max_value": 5},
                required=True,
            ),
        ],
    )

# --- 2. Create a sample SurveyResponse ---
mock_response = SurveyResponse(
    survey_id=mock_survey.id,
    user_id="user-12345",
    id=str(uuid4()),
    answers=[
        Answer(question_id="q1", value="Blue"),
        Answer(question_id="q2", value=["Apple", "Grape"]),
        Answer(question_id="q3", value="The service was great!"),
        Answer(question_id="q4", value=5),
    ],
    completed_at=datetime.datetime.now(),
    duration_seconds=120,
)
