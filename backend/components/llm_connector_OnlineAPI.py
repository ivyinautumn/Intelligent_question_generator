# This is online api version of llm_connector.py, and if use this version, .env should be adapted.

import os
import json
import re
from typing import Dict, Optional, Tuple
import dashscope
from dashscope import Generation
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMConnector:
    """
    Handles connection to the Large Language Model (LLM) and text generation.
    """
    def __init__(self):
        # Retrieve API key and model name from environment variables
        self.api_key = os.getenv('BAILIAN_API_KEY')
        self.model_name = os.getenv('BAILIAN_MODEL_NAME', 'qwen-turbo') # Default to 'qwen-turbo' if not specified

        # Set the DashScope API key
        if self.api_key:
            dashscope.api_key = self.api_key
        else:
            print("Warning: BAILIAN_API_KEY environment variable not found.")

    def generate_text(self, prompt: str) -> Optional[str]:
        """
        Calls the LLM to generate text based on the given prompt.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            Optional[str]: The generated text content from the LLM, or None if an error occurs.
        """
        try:
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                result_format='message' # Request message format output
            )

            if response.status_code == 200:
                # Extract content from the LLM response
                return response.output.choices[0].message.content
            else:
                print(f"LLM generation failed with status code {response.status_code}: {response.message}")
                return None
        except Exception as e:
            print(f"Error during LLM text generation: {e}")
            return None

    def parse_single_choice_json(self, content: str) -> Optional[Dict]:
        """
        Parses the LLM's raw output string to extract single-choice question data in JSON format.

        Args:
            content (str): The raw string content from the LLM.

        Returns:
            Optional[Dict]: A dictionary containing 'question', 'options', 'answer' if parsing is successful,
                            otherwise None.
        """
        try:
            # Use regex to find a JSON object within the content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                question_data = json.loads(json_str)
                # Validate if all required fields are present
                if all(k in question_data for k in ['question', 'options', 'answer']):
                    return {
                        'type': 'single_choice',
                        'question': question_data['question'],
                        'options': question_data['options'],
                        'answer': question_data['answer']
                    }
        except json.JSONDecodeError:
            print("JSONDecodeError: Could not parse single choice question from LLM response.")
        except Exception as e:
            print(f"Error parsing single choice JSON: {e}")
        return None

    def parse_judge_json(self, content: str) -> Optional[Dict]:
        """
        Parses the LLM's raw output string to extract judge question data in JSON format.

        Args:
            content (str): The raw string content from the LLM.

        Returns:
            Optional[Dict]: A dictionary containing 'question', 'answer' if parsing is successful,
                            otherwise None.
        """
        try:
            # Use regex to find a JSON object within the content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                question_data = json.loads(json_str)
                # Validate if all required fields are present
                if all(k in question_data for k in ['question', 'answer']):
                    return {
                        'type': 'judge',
                        'question': question_data['question'],
                        'answer': question_data['answer']
                    }
        except json.JSONDecodeError:
            print("JSONDecodeError: Could not parse judge question from LLM response.")
        except Exception as e:
            print(f"Error parsing judge JSON: {e}")
        return None

    def parse_subjective_json(self, content: str) -> Optional[Dict]:
        """
        Parses the LLM's raw output string to extract subjective question data in JSON format.

        Args:
            content (str): The raw string content from the LLM.

        Returns:
            Optional[Dict]: A dictionary containing 'question', 'answer' if parsing is successful,
                            otherwise None.
        """
        try:
            # Use regex to find a JSON object within the content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                question_data = json.loads(json_str)
                # Validate if all required fields are present
                if all(k in question_data for k in ['question', 'answer']):
                    return {
                        'type': 'subjective',
                        'question': question_data['question'],
                        'answer': question_data['answer']
                    }
        except json.JSONDecodeError:
            print("JSONDecodeError: Could not parse subjective question from LLM response.")
        except Exception as e:
            print(f"Error parsing subjective JSON: {e}")
        return None

    def generate_fallback_single_choice(self, item: Dict) -> Dict:
        """
        Generates a fallback single-choice question if LLM generation fails or produces malformed output.

        Args:
            item (Dict): The document item used as context for the question.

        Returns:
            Dict: A dictionary representing a simple single-choice question.
        """
        return {
            'type': 'single_choice',
            'question': f"关于{item['title']}，以下哪个说法是正确的？",
            'options': [
                "A. 符合相关技术规范要求",
                "B. 不符合相关技术规范要求",
                "C. 需要进一步确认"
            ],
            'answer': "A"
        }

    def generate_fallback_judge(self, item: Dict) -> Dict:
        """
        Generates a fallback judge question if LLM generation fails or produces malformed output.

        Args:
            item (Dict): The document item used as context for the question.

        Returns:
            Dict: A dictionary representing a simple judge question.
        """
        return {
            'type': 'judge',
            'question': f"{item['title']}的相关要求是明确规定的。",
            'answer': "正确"
        }

    def generate_fallback_subjective(self, item: Dict) -> Dict:
        """
        Generates a fallback subjective question if LLM generation fails or produces malformed output.

        Args:
            item (Dict): The document item used as context for the question.

        Returns:
            Dict: A dictionary representing a simple subjective question.
        """
        return {
            'type': 'subjective',
            'question': f"请简要描述{item['title']}的主要内容。",
            'answer': item['text'] # Use the original text as a simple fallback answer
        }

    def judge_subjective_answer_with_llm(self, correct_answer: str, user_answer: str, similarity_threshold: int = 70) -> Tuple[bool, Optional[float]]:
        """
        Uses the LLM to judge the similarity between the correct answer and the user's subjective answer.

        Args:
            correct_answer (str): The expected correct answer.
            user_answer (str): The user's provided answer.
            similarity_threshold (int): The percentage threshold (0-100) for considering answers similar.

        Returns:
            Tuple[bool, Optional[float]]: A tuple where the first element is True if similar, False otherwise,
                                          and the second element is the estimated similarity score (0-100) if available, else None.
        """
        prompt = f"""
请判断以下两个文本的语义相似度，并给出一个0到100的相似度分数。如果相似度分数大于或等于{similarity_threshold}分，则认为它们是“足够接近”的。

正确答案: {correct_answer}
用户答案: {user_answer}

请以JSON格式返回结果，包含 'similarity_score' (整数) 和 'is_similar' (布尔值)。

示例：
{{
    "similarity_score": 85,
    "is_similar": true
}}
"""
        content = self.generate_text(prompt)
        if content:
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    judgment = json.loads(json_str)
                    score = judgment.get('similarity_score')
                    is_similar = judgment.get('is_similar')

                    if isinstance(score, int) and isinstance(is_similar, bool):
                        print(f"LLM judged similarity: Score={score}, Is_similar={is_similar}")
                        return is_similar, score
                    elif isinstance(score, int): # If is_similar is not explicitly returned, use score directly
                        print(f"LLM judged similarity: Score={score}")
                        return score >= similarity_threshold, score
            except json.JSONDecodeError:
                print("JSONDecodeError: Could not parse LLM similarity judgment.")
            except Exception as e:
                print(f"Error parsing LLM similarity judgment: {e}")
        print("LLM failed to judge similarity, defaulting to False.")
        return False, None # Fallback if LLM judgment fails

