
import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from module.models.survey_models import Survey


logger = logging.getLogger(__name__)


def get_survey_dir(storage_dir: Optional[str] = None) -> Path:
    """
    Get the survey storage directory path.

    Args:
        storage_dir: Path to the survey storage directory, uses default if not provided

    Returns:
        Path: Path object of the survey directory
    """
    if storage_dir is None:
        agent_dir = Path(__file__).parent
        storage_dir = agent_dir / "survey"
    else:
        storage_dir = Path(storage_dir)

    storage_dir.mkdir(exist_ok=True)
    return storage_dir

def save_survey_to_file(survey: Survey, survey_dir: Optional[str] = None) -> Optional[Path]:
    """
    Save survey to local file.
    
    Args:
        survey: Survey object
        survey_dir: Path to the survey storage directory, uses default if not provided
        
    Returns:
        Path: Path of the saved file, returns None if failed
    """
    try:
        survey_dir_path = get_survey_dir(survey_dir)
        survey_file = survey_dir_path / f"{survey.id}.json"
        
        with open(survey_file, 'w', encoding='utf-8') as f:
            json.dump(survey.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Survey saved to {survey_file}")
        return survey_file
    except Exception as e:
        logger.error(f"Failed to save survey to file: {e}")
        return None


def load_survey_from_file(survey_id: str, survey_dir: Optional[str] = None) -> Optional[Survey]:
    """
    Load survey from local file based on survey ID.
    
    Args:
        survey_id: Survey ID
        survey_dir: Path to the survey storage directory, uses default if not provided
        
    Returns:
        Survey: Survey object, returns None if not found or failed to load
    """
    try:
        survey_dir_path = get_survey_dir(survey_dir)
        survey_file = survey_dir_path / f"{survey_id}.json"
        
        if not survey_file.exists():
            logger.warning(f"Survey file not found: {survey_file}")
            return None
        
        with open(survey_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        survey = Survey.from_dict(data)
        logger.info(f"Survey loaded from {survey_file}")
        return survey
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse survey JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load survey from file: {e}")
        return None


def list_all_surveys(survey_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List basic information of all saved surveys.
    
    Args:
        survey_dir: Path to the survey storage directory, uses default if not provided
        
    Returns:
        List[Dict]: List of dictionaries containing basic survey information
    """
    try:
        survey_dir_path = get_survey_dir(survey_dir)
        survey_files = list(survey_dir_path.glob("*.json"))
        
        surveys_info = []
        for survey_file in survey_files:
            try:
                with open(survey_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract basic information
                survey_info = {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "target_audience": data.get("target_audience"),
                    "created_at": data.get("created_at"),
                    "question_count": len(data.get("questions", []))
                }
                surveys_info.append(survey_info)
            except Exception as e:
                logger.warning(f"Failed to read survey file {survey_file}: {e}")
                continue
        
        # Sort by creation time (newest
        surveys_info.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        logger.info(f"Found {len(surveys_info)} surveys")
        return surveys_info
    except Exception as e:
        logger.error(f"Failed to list surveys: {e}")
        return []


def delete_survey_file(survey_id: str, survey_dir: Optional[str] = None) -> bool:
    """
    Delete survey file with specified ID.
    
    Args:
        survey_id: Survey ID
        survey_dir: Path to the survey storage directory, uses default if not provided
        
    Returns:
        bool: Returns True if deletion successful, False if failed
    """
    try:
        survey_dir_path = get_survey_dir(survey_dir)
        survey_file = survey_dir_path / f"{survey_id}.json"
        
        if not survey_file.exists():
            logger.warning(f"Survey file not found: {survey_file}")
            return False
        
        survey_file.unlink()
        logger.info(f"Survey file deleted: {survey_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete survey file: {e}")
        return False


def survey_exists(survey_id: str, survey_dir: Optional[str] = None) -> bool:
    """
    Check if survey with specified ID exists.
    
    Args:
        survey_id: Survey ID
        survey_dir: Path to the survey storage directory, uses default if not provided
        
    Returns:
        bool: Returns True if survey exists, False if not found
    """
    try:
        survey_dir_path = get_survey_dir(survey_dir)
        survey_file = survey_dir_path / f"{survey_id}.json"
        return survey_file.exists()
    except Exception as e:
        logger.error(f"Failed to check survey existence: {e}")
        return False
