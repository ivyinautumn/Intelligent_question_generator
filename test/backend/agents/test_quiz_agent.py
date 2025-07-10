import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.agents.quiz_agent import QuizAgent
from backend.components.llm_connector import LLMConnector

def run_quiz_agent_tests():
    """
    Demonstrates the interface and functionality of the QuizAgent class.
    Mocks LLMConnector for subjective answer checking.
    """
    print("--- Testing QuizAgent ---")

    # Mock LLMConnector for subjective answer checking
    mock_llm_connector = MagicMock(spec=LLMConnector)
    # Configure mock for judge_subjective_answer_with_llm
    # First call: similar, Second call: not similar
    mock_llm_connector.judge_subjective_answer_with_llm.side_effect = [
        (True, 80),  # For a similar answer
        (False, 30)  # For a not similar answer
    ]

    quiz_agent = QuizAgent(mock_llm_connector)

    # Test Case 1: check_answer - Single Choice (Correct by letter)
    print("\n--- Test 1: check_answer - Single Choice (Correct by letter) ---")
    question_sc = {"type": "single_choice", "question": "What is 2+2?", "options": ["A. 3", "B. 4", "C. 5"], "answer": "B"}
    user_answer_sc_letter = "B"
    print(f"Input: Question='{question_sc['question']}', User Answer='{user_answer_sc_letter}'")
    is_correct_sc_letter = quiz_agent.check_answer(question_sc, user_answer_sc_letter)
    print(f"Output: {is_correct_sc_letter}") # Expected: True
    assert is_correct_sc_letter is True

    # Test Case 2: check_answer - Single Choice (Correct by full option text)
    print("\n--- Test 2: check_answer - Single Choice (Correct by full option text) ---")
    user_answer_sc_full_text = "B. 4"
    print(f"Input: Question='{question_sc['question']}', User Answer='{user_answer_sc_full_text}'")
    is_correct_sc_full_text = quiz_agent.check_answer(question_sc, user_answer_sc_full_text)
    print(f"Output: {is_correct_sc_full_text}") # Expected: True
    assert is_correct_sc_full_text is True

    # Test Case 3: check_answer - Single Choice (Incorrect)
    print("\n--- Test 3: check_answer - Single Choice (Incorrect) ---")
    user_answer_sc_incorrect = "C"
    print(f"Input: Question='{question_sc['question']}', User Answer='{user_answer_sc_incorrect}'")
    is_correct_sc_incorrect = quiz_agent.check_answer(question_sc, user_answer_sc_incorrect)
    print(f"Output: {is_correct_sc_incorrect}") # Expected: False
    assert is_correct_sc_incorrect is False

    # Test Case 4: check_answer - Judge (Correct)
    print("\n--- Test 4: check_answer - Judge (Correct) ---")
    question_judge = {"type": "judge", "question": "Water boils at 100 degrees Celsius.", "answer": "正确"}
    user_answer_judge_correct = "正确"
    print(f"Input: Question='{question_judge['question']}', User Answer='{user_answer_judge_correct}'")
    is_correct_judge_correct = quiz_agent.check_answer(question_judge, user_answer_judge_correct)
    print(f"Output: {is_correct_judge_correct}") # Expected: True
    assert is_correct_judge_correct is True

    # Test Case 5: check_answer - Judge (Incorrect)
    print("\n--- Test 5: check_answer - Judge (Incorrect) ---")
    user_answer_judge_incorrect = "错误"
    print(f"Input: Question='{question_judge['question']}', User Answer='{user_answer_judge_incorrect}'")
    is_correct_judge_incorrect = quiz_agent.check_answer(question_judge, user_answer_judge_incorrect)
    print(f"Output: {is_correct_judge_incorrect}") # Expected: False
    assert is_correct_judge_incorrect is False

    # Test Case 6: check_answer - Subjective (Similar)
    print("\n--- Test 6: check_answer - Subjective (Similar) ---")
    question_subj = {"type": "subjective", "question": "Explain photosynthesis.", "answer": "Photosynthesis is the process by which green plants convert light energy into chemical energy."}
    user_answer_subj_similar = "Green plants use sunlight to make food through photosynthesis."
    print(f"Input: Question='{question_subj['question']}', Correct Answer='{question_subj['answer']}', User Answer='{user_answer_subj_similar}'")
    is_correct_subj_similar = quiz_agent.check_answer(question_subj, user_answer_subj_similar)
    print(f"Output: {is_correct_subj_similar}") # Expected: True (due to mock)
    assert is_correct_subj_similar is True
    # Verify LLMConnector's method was called
    mock_llm_connector.judge_subjective_answer_with_llm.assert_called_with(
        correct_answer=question_subj['answer'],
        user_answer=user_answer_subj_similar
    )

    # Test Case 7: check_answer - Subjective (Not Similar)
    print("\n--- Test 7: check_answer - Subjective (Not Similar) ---")
    user_answer_subj_not_similar = "The sky is blue."
    print(f"Input: Question='{question_subj['question']}', Correct Answer='{question_subj['answer']}', User Answer='{user_answer_subj_not_similar}'")
    is_correct_subj_not_similar = quiz_agent.check_answer(question_subj, user_answer_subj_not_similar)
    print(f"Output: {is_correct_subj_not_similar}") # Expected: False (due to mock)
    assert is_correct_subj_not_similar is False

    print("\n--- QuizAgent tests completed ---")

if __name__ == "__main__":
    run_quiz_agent_tests()

