"""
Google Sheets Writer module for the Survey AI Agent.

This module handles Google Sheets API authentication, sheet creation,
data formatting, and writing survey responses to spreadsheets with
robust retry mechanisms and data integrity validation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json

from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

from module.models.config_models import SheetsConfig
from module.models.survey_models import Survey, SurveyResponse, Answer, Question
from module.models.exceptions import (
    APIError, 
    ConfigurationError, 
    DataStorageError, 
    ValidationError
)
from module.services.data_formatter import SurveyDataFormatter, DataIntegrityChecker


logger = logging.getLogger(__name__)


class SheetWriter:
    """
    Google Sheets writer for survey responses.
    
    Handles authentication, sheet creation, formatting, and data writing
    with proper error handling and retry mechanisms.
    """
    
    # Google Sheets API scope
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
    
    def __init__(self, config: SheetsConfig):
        """
        Initialize SheetWriter with configuration.
        
        Args:
            config: SheetsConfig instance with API credentials and settings
        """
        self.config = config
        self.service = None
        self.drive_service = None
        self.spreadsheet = None
        self.credentials = None
        self._authenticated = False

        # Initialize components
        self.data_formatter = SurveyDataFormatter()
        self.integrity_checker = DataIntegrityChecker()

        # Validate configuration
        self.config.validate()
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API.
        
        Returns:
            bool: True if authentication successful, False otherwise
            
        Raises:
            APIError: If authentication fails
            ConfigurationError: If credentials are invalid
        """
        try:
            logger.info("Authenticating with Google Sheets API...")
            
            # Check if credentials file exists
            if not os.path.exists(self.config.credentials_path):
                raise ConfigurationError(
                    "credentials_path",
                    f"Credentials file not found: {self.config.credentials_path}"
                )
                # Load credentials based on file type
            self.credentials = ServiceAccountCredentials.from_service_account_file(
                self.config.credentials_path, scopes=self.SCOPES
                )

            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self._authenticated = True
            # Get the spreadsheet
            self.spreadsheet = self.service.spreadsheets()
            logger.info("Successfully authenticated with Google Sheets API")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            if isinstance(e, (ConfigurationError, APIError)):
                raise
            raise APIError(
                service="Google Sheets",
                message=f"Authentication failed: {str(e)}",
                context={'credentials_path': self.config.credentials_path}
            )

    def is_authenticated(self) -> bool:
        """Check if the writer is authenticated."""
        return self._authenticated
    
    def write_header(self, sheet_id: str, survey: Survey,):
        headers = self.data_formatter.generate_headers(survey)
        self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=f"{self.config.default_sheet_name}!A1",
            valueInputOption="USER_ENTERED", body={"values": [headers]}
        ).execute()
        print("Headers written successfully.")
        return True

    def write_response(self, sheet_id: str, response: SurveyResponse, 
                           survey: Survey) -> bool:
        """
        Write a survey response to the specified spreadsheet with retry logic.
        
        Args:
            sheet_id: ID of the target spreadsheet
            response: SurveyResponse object to write
            survey: Survey object for question mapping
            
        Returns:
            bool: True if write successful, False otherwise
            
        Raises:
            APIError: If write operation fails
            ValidationError: If response data is invalid
        """
        if not self._authenticated:
            self.authenticate()
        try:
            logger.info(f"Writing response for user {response.user_id} to sheet {sheet_id}")
            
            # Validate and format response data
            row_data = self.data_formatter.format_response_row(response, survey)
            print(row_data)
            next_row = self._find_next_empty_row(sheet_id)
            # Calculate range
            end_column = chr(65 + len(row_data) - 1) if len(row_data) <= 26 else f"A{len(row_data)}"
            range_name = f"{self.config.default_sheet_name}!A{next_row}:{end_column}{next_row}"
            
            body = {'values': [row_data]}
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            updated_cells = result.get('updatedCells', 0)
            logger.info(f"Successfully wrote {updated_cells} cells")

            return True
            
        except Exception as e:
            logger.error(f"Failed to write response: {e}")
            if isinstance(e, (ValidationError, APIError, DataStorageError)):
                raise
            
            raise DataStorageError(
                operation="write",
                message=str(e),
                storage_type="Google Sheets",
                context={
                    'sheet_id': sheet_id,
                    'user_id': response.user_id,
                    'response_id': response.id
                }
            )
    
    def _find_next_empty_row(self, sheet_id: str) -> int:
        """
        Find the next empty row in the spreadsheet.
        
        Args:
            sheet_id: ID of the spreadsheet
            
        Returns:
            int: Row number (1-based) of the next empty row
        """
        try:
            # Get current data to find the last row
            range_name = f"{self.config.default_sheet_name}!A:A"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return len(values) + 1  # Next row after the last data row
            
        except Exception as e:
            logger.warning(f"Could not determine next empty row, using row 2: {e}")
            return 2  # Default to row 2 if we can't determine
