import os
import json
from typing import List, Dict, Any, Optional
import random

class DataLoader:
    """
    Handles all file system operations related to raw documents and question banks.
    """
    def __init__(self):
        # Update paths to point to the new 'data' directory
        self.base_data_dir = 'data'
        self.raw_file_dir = os.path.join(self.base_data_dir, 'raw_files') # Changed from 'raw_file'
        self.question_dataset_dir = os.path.join(self.base_data_dir, 'question_dataset')

        # Ensure directories exist
        os.makedirs(self.raw_file_dir, exist_ok=True)
        os.makedirs(self.question_dataset_dir, exist_ok=True)

    def validate_json_format(self, data: List[Dict]) -> bool:
        """
        Validates if the JSON file content adheres to the required format for technical documents.

        Args:
            data (List[Dict]): The parsed JSON data.

        Returns:
            bool: True if the format is valid, False otherwise.
        """
        try:
            if not isinstance(data, list):
                return False

            for item in data:
                if not isinstance(item, dict):
                    return False

                # Check for required fields and their types
                required_fields = ['idx', 'title', 'text']
                for field in required_fields:
                    if field not in item:
                        return False
                    if not isinstance(item[field], str):
                        return False
            return True
        except Exception as e:
            print(f"Error validating JSON format: {e}")
            return False

    def save_uploaded_file(self, uploaded_file) -> str:
        """
        Saves an uploaded file to the raw_files directory.

        Args:
            uploaded_file: The uploaded file object from Streamlit.

        Returns:
            str: The full path to the saved file.
        """
        file_path = os.path.join(self.raw_file_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        return file_path

    def get_uploaded_files(self) -> List[str]:
        """
        Retrieves a list of all JSON files in the raw_files directory.

        Returns:
            List[str]: A sorted list of filenames.
        """
        try:
            files = []
            for filename in os.listdir(self.raw_file_dir):
                if filename.endswith('.json'):
                    files.append(filename)
            return sorted(files)
        except Exception as e:
            print(f"Error getting uploaded files: {e}")
            return []

    def get_question_banks(self) -> List[str]:
        """
        Retrieves a list of available question banks (JSON files) from the question_dataset directory.

        Returns:
            List[str]: A sorted list of question bank names (without extension).
        """
        try:
            banks = []
            for filename in os.listdir(self.question_dataset_dir):
                if filename.endswith('.json'):
                    bank_name = filename[:-5] # Remove .json extension
                    banks.append(bank_name)
            return sorted(banks)
        except Exception as e:
            print(f"Error getting question banks: {e}")
            return []

    def load_document(self, filename: str) -> List[Dict]:
        """
        Loads a technical specification document from the raw_files directory.

        Args:
            filename (str): The name of the document file.

        Returns:
            List[Dict]: The parsed content of the document, or an empty list if loading fails.
        """
        file_path = os.path.join(self.raw_file_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Document file not found: {file_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from document file: {file_path}")
            return []
        except Exception as e:
            print(f"Error loading document {filename}: {e}")
            return []

    def load_question_bank_by_name(self, bank_name_without_ext: str) -> List[Dict]:
        """
        Loads a question bank file by its name (without extension).

        Args:
            bank_name_without_ext (str): The name of the question bank.

        Returns:
            List[Dict]: The parsed content of the question bank, or an empty list if not found or loading fails.
        """
        bank_path = os.path.join(self.question_dataset_dir, f"{bank_name_without_ext}.json")
        if os.path.exists(bank_path):
            try:
                with open(bank_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Question bank {bank_path} is corrupted, returning empty list.")
                return []
            except Exception as e:
                print(f"Error loading question bank {bank_name_without_ext}: {e}")
                return []
        return []

    def save_question_bank(self, question_filename: str, questions: List[Dict]) -> str:
        """
        Saves a list of questions to a specified question bank file.

        Args:
            question_filename (str): The name of the question bank file (e.g., "my_bank.json").
            questions (List[Dict]): The list of questions to save.

        Returns:
            str: The full path to the saved question bank file.
        """
        question_path = os.path.join(self.question_dataset_dir, question_filename)
        try:
            with open(question_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            return question_path
        except Exception as e:
            print(f"Error saving question bank {question_filename}: {e}")
            return ""

    def load_questions_for_quiz(self, bank_name: str, count: int) -> List[Dict]:
        """
        Loads a specified number of random questions from a question bank for a quiz.

        Args:
            bank_name (str): The name of the question bank (without extension).
            count (int): The number of questions to load.

        Returns:
            List[Dict]: A list of randomly selected questions, or an empty list if loading fails.
        """
        try:
            bank_path = os.path.join(self.question_dataset_dir, f"{bank_name}.json")
            with open(bank_path, 'r', encoding='utf-8') as f:
                all_questions = json.load(f)

            # Randomly select questions, ensuring not to select more than available
            selected_questions = random.sample(all_questions, min(count, len(all_questions)))
            return selected_questions
        except FileNotFoundError:
            print(f"Question bank file not found: {bank_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from question bank file: {bank_path}")
            return []
        except Exception as e:
            print(f"Error loading questions for quiz from {bank_name}: {e}")
            return []

