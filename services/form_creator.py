from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from auth.auth import get_credentials
from config import APP_TITLE

logger = logging.getLogger(__name__)

def create_form(mcqs, title=None):
    """
    Create a Google Form with the given MCQs.

    Args:
        mcqs (list): List of MCQ dictionaries.
        title (str): Title for the form.

    Returns:
        str: URL to the created form.
    """
    if not mcqs:
        raise ValueError("No questions provided to create form")

    if not title:
        title = f"{APP_TITLE} Quiz"

    try:
        creds = get_credentials()
        service = build("forms", "v1", credentials=creds)

        # Create form
        form = service.forms().create(body={
            "info": {"title": title}
        }).execute()
        form_id = form["formId"]
        logger.info(f"Created Google Form: {form_id}")

        # Enable quiz grading
        service.forms().batchUpdate(
            formId=form_id,
            body={
                "requests": [
                    {
                        "updateSettings": {
                            "settings": {
                                "quizSettings": {"isQuiz": True}
                            },
                            "updateMask": "quizSettings"
                        }
                    }
                ]
            }
        ).execute()

        # Add quiz questions with grading
        requests = []
        for q in mcqs:
            if not all(key in q for key in ["question", "options", "answer"]):
                logger.warning(f"Skipping invalid question: {q}")
                continue

            correct_answer = q["answer"]
            requests.append({
                "createItem": {
                    "item": {
                        "title": q["question"],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "grading": {
                                    "pointValue": 1,
                                    "correctAnswers": {
                                        "answers": [{"value": correct_answer}]
                                    }
                                },
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value": opt} for opt in q["options"]],
                                    "shuffle": True
                                }
                            }
                        }
                    },
                    "location": {"index": 0}
                }
            })

        if requests:
            service.forms().batchUpdate(
                formId=form_id,
                body={"requests": requests}
            ).execute()
            logger.info(f"Added {len(requests)} questions to form")

        # Publish form so it has a shareable responder link
        try:
            service.forms().setPublishSettings(
                formId=form_id,
                body={
                    "publishSettings": {
                        "publishState": "PUBLISHED",
                        "isAcceptingResponses": True
                    }
                }
            ).execute()
        except HttpError as e:
            logger.warning(f"Could not publish form: {e}")

        published_form = service.forms().get(formId=form_id).execute()
        responder_uri = published_form.get("responderUri")
        if responder_uri:
            return responder_uri

        return f"https://docs.google.com/forms/d/{form_id}/viewform"

    except HttpError as e:
        logger.error(f"Google API error: {e}")
        raise Exception(f"Failed to create Google Form: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in create_form: {e}")
        raise Exception(f"Failed to create form: {e}")