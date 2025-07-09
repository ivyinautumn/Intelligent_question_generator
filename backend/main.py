import os
import sys
from typing import List, Dict, Any

# Add project root to Python path to ensure imports work correctly
# This assumes the script is run from the project root or a subdirectory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the refactored components and agents
from backend.components.llm_connector import LLMConnector
from backend.components.data_loader import DataLoader
from backend.agents.question_agent import QuestionAgent
from backend.agents.quiz_agent import QuizAgent

class QuestionSystemBackend:
    """
    Main backend class for the Question System.
    Orchestrates interactions between data loading, LLM, question generation, and quiz management.
    """
    def __init__(self):
        # Initialize components
        self.data_loader = DataLoader()
        self.llm_connector = LLMConnector()

        # Initialize agents with their required dependencies
        self.question_agent = QuestionAgent(self.llm_connector, self.data_loader)
        # Pass llm_connector to QuizAgent for subjective answer checking
        self.quiz_agent = QuizAgent(self.llm_connector)

        # Print initialization status (optional)
        print("QuestionSystemBackend initialized successfully.")

    # --- Document Management Methods (Delegated to DataLoader) ---
    def validate_json_format(self, data: List[Dict]) -> bool:
        """Delegates to DataLoader to validate JSON format."""
        return self.data_loader.validate_json_format(data)

    def save_uploaded_file(self, uploaded_file) -> str:
        """Delegates to DataLoader to save an uploaded file."""
        return self.data_loader.save_uploaded_file(uploaded_file)

    def get_uploaded_files(self) -> List[str]:
        """Delegates to DataLoader to get a list of uploaded files."""
        return self.data_loader.get_uploaded_files()

    def get_question_banks(self) -> List[str]:
        """Delegates to DataLoader to get a list of available question banks."""
        return self.data_loader.get_question_banks()

    # --- Question Generation Methods (Delegated to QuestionAgent) ---
    def generate_questions(self, filename: str, count: int) -> List[Dict]:
        """Delegates to QuestionAgent to generate questions."""
        return self.question_agent.generate_questions(filename, count)

    def save_question_bank(self, source_filename: str, new_questions: List[Dict]) -> str:
        """Delegates to QuestionAgent to save (and merge/deduplicate) a question bank."""
        return self.question_agent.save_question_bank(source_filename, new_questions)

    # --- Quiz Management Methods (Delegated to DataLoader and QuizAgent) ---
    def load_questions_for_quiz(self, bank_name: str, count: int) -> List[Dict]:
        """Delegates to DataLoader to load questions for a quiz."""
        return self.data_loader.load_questions_for_quiz(bank_name, count)

    def check_answer(self, question: Dict, user_answer: str) -> bool:
        """Delegates to QuizAgent to check an answer."""
        return self.quiz_agent.check_answer(question, user_answer)

