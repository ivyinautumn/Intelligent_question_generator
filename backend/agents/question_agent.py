import os
import json
import random
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz # Used for fuzzy matching to check question similarity

# Import components
from backend.components.llm_connector import LLMConnector
from backend.components.data_loader import DataLoader

class QuestionAgent:
    """
    Handles the logic for generating questions, checking similarity, and managing question banks.
    """
    def __init__(self, llm_connector: LLMConnector, data_loader: DataLoader):
        self.llm_connector = llm_connector
        self.data_loader = data_loader

    def _is_similar_question(self, new_question: Dict, existing_questions: List[Dict], threshold: int = 80) -> bool:
        """
        Checks if a newly generated question is similar to any existing questions using fuzzy matching.
        Note: For subjective questions, this only checks the question text, not the answer.
        Subjective answer similarity is handled by LLM in quiz_agent.

        Args:
            new_question (Dict): The new question to check.
            existing_questions (List[Dict]): A list of questions to compare against.
            threshold (int): The similarity threshold (0-100). Questions with similarity >= threshold are considered similar.

        Returns:
            bool: True if a similar question is found, False otherwise.
        """
        new_q_text = new_question['question'].strip()
        new_q_type = new_question['type']

        for existing_q in existing_questions:
            existing_q_text = existing_q['question'].strip()
            existing_q_type = existing_q['type']

            # Only compare questions of the same type for strict similarity check
            if new_q_type != existing_q_type:
                continue

            # Use fuzzy matching to check similarity of question text
            similarity = fuzz.ratio(new_q_text, existing_q_text)
            if similarity >= threshold:
                # For single-choice questions, also consider options similarity
                if new_q_type == 'single_choice' and 'options' in new_question and 'options' in existing_q:
                    # Check if at least one option is highly similar
                    option_similarity_found = False
                    for new_opt in new_question['options']:
                        for existing_opt in existing_q['options']:
                            if fuzz.ratio(new_opt, existing_opt) >= threshold:
                                option_similarity_found = True
                                break
                        if option_similarity_found:
                            break
                    if option_similarity_found:
                        print(f"Detected similar question (Similarity: {similarity}%):")
                        print(f"  New: {new_q_text}")
                        print(f"  Existing: {existing_q_text}")
                        return True
                else: # For judge and subjective questions, only question text similarity is checked here
                    print(f"Detected similar question (Similarity: {similarity}%):")
                    print(f"  New: {new_q_text}")
                    print(f"  Existing: {existing_q_text}")
                    return True
        return False

    def _generate_single_choice_question(self, item: Dict) -> Optional[Dict]:
        """
        Generates a single-choice question using the LLM based on a document item.

        Args:
            item (Dict): The document item (section) to base the question on.

        Returns:
            Optional[Dict]: A dictionary representing the generated single-choice question, or None if generation fails.
        """
        prompt = f"""
基于以下技术规范内容，生成一道单选题：

标题: {item['title']}
内容: {item['text']}

请生成一道单选题，要求：
1. 题目应该考查对该技术规范的理解
2. 提供3个选项，其中1个正确答案，2个错误答案
3. 错误答案应该是合理的干扰项
4. 返回JSON格式，包含question、options、answer字段

返回格式示例：
{{
    "question": "问题内容",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3"],
    "answer": "A"
}}
"""
        content = self.llm_connector.generate_text(prompt)
        if content:
            question_data = self.llm_connector.parse_single_choice_json(content)
            if question_data:
                return question_data
        # Fallback if LLM generation fails or parsing is unsuccessful
        return self.llm_connector.generate_fallback_single_choice(item)

    def _generate_judge_question(self, item: Dict) -> Optional[Dict]:
        """
        Generates a judge (true/false) question using the LLM based on a document item.

        Args:
            item (Dict): The document item (section) to base the question on.

        Returns:
            Optional[Dict]: A dictionary representing the generated judge question, or None if generation fails.
        """
        prompt = f"""
基于以下技术规范内容，生成一道判断题：

标题: {item['title']}
内容: {item['text']}

请生成一道判断题，要求：
1. 题目应该考查对该技术规范的理解
2. 可以是正确的陈述或错误的陈述
3. 返回JSON格式，包含question、answer字段

返回格式示例：
{{
    "question": "问题内容",
    "answer": "正确"
}}
"""
        content = self.llm_connector.generate_text(prompt)
        if content:
            question_data = self.llm_connector.parse_judge_json(content)
            if question_data:
                return question_data
        # Fallback if LLM generation fails or parsing is unsuccessful
        return self.llm_connector.generate_fallback_judge(item)

    def _generate_subjective_question(self, item: Dict) -> Optional[Dict]:
        """
        Generates a subjective question using the LLM based on a document item.

        Args:
            item (Dict): The document item (section) to base the question on.

        Returns:
            Optional[Dict]: A dictionary representing the generated subjective question, or None if generation fails.
        """
        prompt = f"""
基于以下技术规范内容，生成一道主观题（问答题）：

标题: {item['title']}
内容: {item['text']}

请生成一道主观题，要求：
1. 题目应该考查对该技术规范内容的理解和阐述能力
2. 提供一个简洁明了的标准答案
3. 返回JSON格式，包含question、answer字段

返回格式示例：
{{
    "question": "请阐述在进行'停电抄表及显示'时，电能表应具备哪些特性或操作流程？",
    "answer": "电能表在停电情况下，可通过按键唤醒显示，显示内容应包含重要结算数据，并且所有数据应能在断电情况下至少保存10年。"
}}
"""
        content = self.llm_connector.generate_text(prompt)
        if content:
            question_data = self.llm_connector.parse_subjective_json(content)
            if question_data:
                return question_data
        # Fallback if LLM generation fails or parsing is unsuccessful
        return self.llm_connector.generate_fallback_subjective(item)

    def generate_questions(self, filename: str, count: int) -> List[Dict]:
        """
        Generates a specified number of questions (single-choice, judge, or subjective) from a given document.
        Includes similarity checking to avoid duplicate or very similar questions.

        Args:
            filename (str): The name of the document file to generate questions from.
            count (int): The desired number of questions to generate.

        Returns:
            List[Dict]: A list of generated questions.
        """
        try:
            document = self.data_loader.load_document(filename)
            if not document:
                print(f"Document {filename} is empty or failed to load.")
                return []

            # Get existing questions from the corresponding question bank for deduplication
            base_name = os.path.splitext(filename)[0]
            existing_questions_in_bank = self.data_loader.load_question_bank_by_name(f"{base_name}题库")
            print(f"Loaded {len(existing_questions_in_bank)} existing questions from {base_name}题库.json for similarity check.")

            generated_questions = []
            attempt_count = 0
            max_attempts_per_question = 5 # Max attempts to generate a unique question from one item
            max_total_attempts = count * max_attempts_per_question * 2 # Increased total attempts to ensure enough unique questions

            question_types = ['single_choice', 'judge', 'subjective'] # Include subjective questions

            while len(generated_questions) < count and attempt_count < max_total_attempts:
                item = random.choice(document) if document else None
                if not item:
                    break

                question_type = random.choice(question_types)
                new_question = None

                if question_type == 'single_choice':
                    new_question = self._generate_single_choice_question(item)
                elif question_type == 'judge':
                    new_question = self._generate_judge_question(item)
                elif question_type == 'subjective':
                    new_question = self._generate_subjective_question(item)

                attempt_count += 1

                if new_question:
                    # Check similarity against already generated questions in this session and existing bank questions
                    if not self._is_similar_question(new_question, generated_questions + existing_questions_in_bank):
                        # Assign a temporary index and source file for the newly generated question
                        new_question['idx'] = len(generated_questions) + 1
                        new_question['source_file'] = filename
                        generated_questions.append(new_question)
                    else:
                        print(f"Skipping similar question: {new_question.get('question', 'Unknown question')[:30]}...")
                else:
                    print(f"Failed to generate a question for item: {item.get('title', 'Unknown Title')}")

            print(f"Generated {len(generated_questions)} unique questions. Total attempts: {attempt_count}")
            return generated_questions
        except Exception as e:
            print(f"Error during question generation: {e}")
            return []

    def save_question_bank(self, source_filename: str, new_questions: List[Dict]) -> str:
        """
        Saves a new set of questions to a question bank.
        If a bank with the same name exists, it merges new questions and deduplicates them.

        Args:
            source_filename (str): The original document filename (e.g., "doc.json").
            new_questions (List[Dict]): The list of newly generated questions.

        Returns:
            str: The filename of the saved question bank.
        """
        base_name = os.path.splitext(source_filename)[0]
        question_filename = f"{base_name}题库.json"

        all_questions = []
        # Load existing questions if the bank already exists
        existing_questions = self.data_loader.load_question_bank_by_name(f"{base_name}题库")
        if existing_questions:
            all_questions.extend(existing_questions)
            print(f"Detected existing question bank {question_filename}, containing {len(existing_questions)} questions.")

        # Use a set to track question texts for exact deduplication
        # For subjective questions, only question text is used for deduplication here.
        seen_questions_text = set(q['question'] for q in all_questions)
        added_count = 0

        for q in new_questions:
            if q['question'] not in seen_questions_text:
                all_questions.append(q)
                seen_questions_text.add(q['question'])
                added_count += 1
            else:
                print(f"Skipping exactly duplicate question: {q['question'][:30]}...")

        # Re-index all questions to ensure sequential `idx`
        for i, q in enumerate(all_questions):
            q['idx'] = i + 1

        saved_path = self.data_loader.save_question_bank(question_filename, all_questions)

        print(f"Added {added_count} new questions to {question_filename}.")
        print(f"Question bank now contains {len(all_questions)} questions.")
        return os.path.basename(saved_path) # Return only the filename

