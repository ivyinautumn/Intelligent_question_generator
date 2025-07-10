import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add project root to Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.components.llm_connector import LLMConnector

def run_llm_connector_tests():
    """
    Demonstrates the interface and functionality of the LLMConnector class.
    Mocks the dashscope.Generation.call method to avoid actual API calls.
    """
    print("--- Testing LLMConnector ---")

    # Mock the dashscope.Generation.call method
    with patch('dashscope.Generation.call') as mock_llm_call:
        llm_connector = LLMConnector()

        # Mock LLM response for generate_text
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.output.choices = [MagicMock()]
        mock_response_obj.output.choices[0].message.content = "Mocked LLM response content."
        mock_llm_call.return_value = mock_response_obj

        # Test Case 1: generate_text
        print("\n--- Test 1: generate_text ---")
        test_prompt = "Generate a short text about AI."
        print(f"Input (generate_text): Prompt='{test_prompt}'")
        generated_text = llm_connector.generate_text(test_prompt)
        print(f"Output (generate_text): '{generated_text}'") # Expected: "Mocked LLM response content."
        assert generated_text == "Mocked LLM response content."

        # Test Case 2: parse_single_choice_json
        print("\n--- Test 2: parse_single_choice_json ---")
        mock_single_choice_json_str = """
        {
            "question": "Which of the following is an input device?",
            "options": ["A. Monitor", "B. Keyboard", "C. Printer"],
            "answer": "B"
        }
        """
        print(f"Input (parse_single_choice_json): JSON string")
        parsed_single_choice = llm_connector.parse_single_choice_json(mock_single_choice_json_str)
        print(f"Output (parse_single_choice_json): {parsed_single_choice}")
        assert parsed_single_choice['type'] == 'single_choice'
        assert parsed_single_choice['question'] == "Which of the following is an input device?"

        # Test Case 3: parse_judge_json
        print("\n--- Test 3: parse_judge_json ---")
        mock_judge_json_str = """
        {
            "question": "The sun revolves around the Earth.",
            "answer": "错误"
        }
        """
        print(f"Input (parse_judge_json): JSON string")
        parsed_judge = llm_connector.parse_judge_json(mock_judge_json_str)
        print(f"Output (parse_judge_json): {parsed_judge}")
        assert parsed_judge['type'] == 'judge'
        assert parsed_judge['question'] == "The sun revolves around the Earth."

        # Test Case 4: parse_subjective_json
        print("\n--- Test 4: parse_subjective_json ---")
        mock_subjective_json_str = """
        {
            "question": "Explain the concept of photosynthesis.",
            "answer": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods with the help of chlorophyll."
        }
        """
        print(f"Input (parse_subjective_json): JSON string")
        parsed_subjective = llm_connector.parse_subjective_json(mock_subjective_json_str)
        print(f"Output (parse_subjective_json): {parsed_subjective}")
        assert parsed_subjective['type'] == 'subjective'
        assert parsed_subjective['question'] == "Explain the concept of photosynthesis."

        # Test Case 5: generate_fallback_single_choice
        print("\n--- Test 5: generate_fallback_single_choice ---")
        mock_item = {"title": "Test Title", "text": "Test Text"}
        fallback_sc = llm_connector.generate_fallback_single_choice(mock_item)
        print(f"Input (generate_fallback_single_choice): Item={mock_item}")
        print(f"Output (generate_fallback_single_choice): {fallback_sc}")
        assert fallback_sc['type'] == 'single_choice'

        # Test Case 6: generate_fallback_judge
        print("\n--- Test 6: generate_fallback_judge ---")
        fallback_judge = llm_connector.generate_fallback_judge(mock_item)
        print(f"Input (generate_fallback_judge): Item={mock_item}")
        print(f"Output (generate_fallback_judge): {fallback_judge}")
        assert fallback_judge['type'] == 'judge'

        # Test Case 7: generate_fallback_subjective
        print("\n--- Test 7: generate_fallback_subjective ---")
        fallback_subjective = llm_connector.generate_fallback_subjective(mock_item)
        print(f"Input (generate_fallback_subjective): Item={mock_item}")
        print(f"Output (generate_fallback_subjective): {fallback_subjective}")
        assert fallback_subjective['type'] == 'subjective'

        # Test Case 8: judge_subjective_answer_with_llm (mocking LLM response for judgment)
        print("\n--- Test 8: judge_subjective_answer_with_llm ---")
        mock_llm_call.return_value.output.choices[0].message.content = json.dumps({
            "similarity_score": 85,
            "is_similar": True
        })
        correct_ans = "Photosynthesis is the process by which green plants convert light energy into chemical energy."
        user_ans = "Green plants use sunlight to make food through photosynthesis."
        print(f"Input (judge_subjective_answer_with_llm): Correct='{correct_ans}', User='{user_ans}'")
        is_similar, score = llm_connector.judge_subjective_answer_with_llm(correct_ans, user_ans)
        print(f"Output (judge_subjective_answer_with_llm): Is_similar={is_similar}, Score={score}")
        assert is_similar is True
        assert score == 85

        mock_llm_call.return_value.output.choices[0].message.content = json.dumps({
            "similarity_score": 40,
            "is_similar": False
        })
        is_similar, score = llm_connector.judge_subjective_answer_with_llm(correct_ans, "This is a completely different answer.")
        print(f"Input (judge_subjective_answer_with_llm): Correct='{correct_ans}', User='This is a completely different answer.'")
        print(f"Output (judge_subjective_answer_with_llm): Is_similar={is_similar}, Score={score}")
        assert is_similar is False
        assert score == 40

    print("\n--- LLMConnector tests completed ---")

if __name__ == "__main__":
    run_llm_connector_tests()

