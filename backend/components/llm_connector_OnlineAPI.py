# This is online api version of llm_connector.py, and if use this version, .env should be adapted.

import os
import json
import re
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

class LLMConnector:
    """
    Handles connection to the Large Language Model (LLM) and text generation.
    """
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY', 'sk-no-key-required')
        self.base_url = os.getenv('OPENAI_API_BASE', 'http://localhost:8000/v1')
        self.model_name = os.getenv('OPENAI_MODEL_NAME', 'Qwen2.5-7B-Instruct')

        try:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            print(f"LLMConnector initialized with base_url: {self.base_url}, model: {self.model_name}")
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.client = None


    def generate_text(self, prompt: str) -> Optional[str]:
        """
        Calls the LLM to generate text based on the given prompt.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            Optional[str]: The generated text content from the LLM, or None if an error occurs.
        """
        if not self.client:
            print("LLM client not initialized.")
            return None
        try:
            # 确保输入是UTF-8编码
            # prompt = str(prompt).encode('utf-8').decode('utf-8')

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt} # 使用处理过的提示词
                ],
                temperature=0.1,
                max_tokens=2048,
            )

            if response.choices and response.choices[0].message and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                print(f"LLM generation returned no content.")
                return None
        except openai.APIConnectionError as e:
            print(f"Could not connect to OpenAI API: {e}")
            print(f"Please ensure your local LLM server is running at {self.base_url}")
            return None
        except openai.RateLimitError as e:
            print(f"OpenAI API request exceeded rate limit: {e}")
            return None
        except openai.APIStatusError as e:
            print(f"OpenAI API returned an error status: {e.status_code} - {e.response}")
            return None
        except Exception as e:
            print(f"Error during LLM text generation: {e}")
            return None

    def parse_single_choice_json(self, content: str) -> Optional[Dict]:
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                question_data = json.loads(json_str)
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
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                question_data = json.loads(json_str)
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
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                question_data = json.loads(json_str)
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
        return {
            'type': 'judge',
            'question': f"{item['title']}的相关要求是明确规定的。",
            'answer': "正确"
        }

    def generate_fallback_subjective(self, item: Dict) -> Dict:
        return {
            'type': 'subjective',
            'question': f"请简要描述{item['title']}的主要内容。",
            'answer': item['text']
        }

    def judge_subjective_answer_with_llm(self, correct_answer: str, user_answer: str, similarity_threshold: int = 70) -> Tuple[bool, Optional[float]]:
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
                    elif isinstance(score, int):
                        print(f"LLM judged similarity: Score={score}")
                        return score >= similarity_threshold, score
            except json.JSONDecodeError:
                print("JSONDecodeError: Could not parse LLM similarity judgment.")
            except Exception as e:
                print(f"Error parsing LLM similarity judgment: {e}")
        print("LLM failed to judge similarity, defaulting to False.")
        return False, None