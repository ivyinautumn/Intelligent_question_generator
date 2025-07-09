import re
from typing import Dict, List
from backend.components.llm_connector import LLMConnector # Import LLMConnector

class QuizAgent:
    """
    Handles the logic for taking a quiz and checking answers.
    """
    def __init__(self, llm_connector: LLMConnector): # Accept LLMConnector
        self.llm_connector = llm_connector

    def check_answer(self, question: Dict, user_answer: str) -> bool:
        """
        Checks if the user's answer is correct for a given question.
        Supports single-choice (by letter or full option text), judge, and subjective questions.

        Args:
            question (Dict): The question dictionary, including 'type', 'answer', and potentially 'options'.
            user_answer (str): The user's input answer.

        Returns:
            bool: True if the answer is correct, False otherwise.
        """
        try:
            correct_answer = str(question['answer']).lower().strip()
            user_answer = user_answer.lower().strip()

            if question['type'] == 'single_choice':
                # Single choice question: check against letter (A, B, C) or full option text
                # Correct answer is typically 'A', 'B', 'C'
                # User answer can be 'a', 'b', 'c' or 'a. option content'

                # 1. Direct comparison if user answer is just the letter
                if user_answer == correct_answer:
                    return True

                # 2. If user input is the full option text, try to match
                if 'options' in question and isinstance(question['options'], list):
                    for option in question['options']:
                        if option.lower().strip() == user_answer:
                            # Extract the letter from the option (e.g., "A. Option Text" -> "A")
                            option_letter_match = re.match(r'([a-d])\.', option, re.IGNORECASE)
                            if option_letter_match and option_letter_match.group(1).lower() == correct_answer:
                                return True
                return False

            elif question['type'] == 'judge':
                # Judge question: supports multiple formats for "True" and "False"
                positive_answers = ['正确', '对', '是', 'true', 'yes', '√']
                negative_answers = ['错误', '不对', '否', 'false', 'no', '×']

                if correct_answer in positive_answers:
                    return user_answer in positive_answers
                elif correct_answer in negative_answers:
                    return user_answer in negative_answers
                else:
                    # If the correct answer is not in standard positive/negative formats,
                    # perform a strict match
                    return user_answer == correct_answer
            elif question['type'] == 'subjective':
                # For subjective questions, use LLM to judge semantic similarity
                is_similar, _ = self.llm_connector.judge_subjective_answer_with_llm(
                    correct_answer=question['answer'], # Use original case for LLM if possible
                    user_answer=user_answer # Use original case for LLM if possible
                )
                return is_similar
            return False
        except Exception as e:
            print(f"Error checking answer: {e}")
            return False

