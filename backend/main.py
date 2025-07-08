import os
import json
import random
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import dashscope
from dashscope import Generation
from dotenv import load_dotenv
from fuzzywuzzy import fuzz # 新增：用于模糊匹配，查重题目相似度

# 加载环境变量
load_dotenv()

class QuestionSystemBackend:
    def __init__(self):
        self.api_key = os.getenv('BAILIAN_API_KEY')
        self.model_name = os.getenv('BAILIAN_MODEL_NAME', 'qwen-turbo')
        self.raw_file_dir = 'raw_file'
        self.question_dataset_dir = 'question_dataset'
        
        # 确保目录存在
        os.makedirs(self.raw_file_dir, exist_ok=True)
        os.makedirs(self.question_dataset_dir, exist_ok=True)
        
        # 设置API密钥
        if self.api_key:
            dashscope.api_key = self.api_key
        else:
            print("警告: 未找到BAILIAN_API_KEY环境变量")
    
    def validate_json_format(self, data: List[Dict]) -> bool:
        """验证JSON文件格式是否符合要求"""
        try:
            if not isinstance(data, list):
                return False
            
            for item in data:
                if not isinstance(item, dict):
                    return False
                
                # 检查必要字段
                required_fields = ['idx', 'title', 'text']
                for field in required_fields:
                    if field not in item:
                        return False
                    if not isinstance(item[field], str):
                        return False
                
            return True
        except Exception:
            return False
    
    def save_uploaded_file(self, uploaded_file) -> str:
        """保存上传的文件"""
        file_path = os.path.join(self.raw_file_dir, uploaded_file.name)
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        return file_path
    
    def get_uploaded_files(self) -> List[str]:
        """获取已上传的文件列表"""
        try:
            files = []
            for filename in os.listdir(self.raw_file_dir):
                if filename.endswith('.json'):
                    files.append(filename)
            return sorted(files)
        except Exception:
            return []
    
    def get_question_banks(self) -> List[str]:
        """获取可用的题库列表"""
        try:
            banks = []
            for filename in os.listdir(self.question_dataset_dir):
                if filename.endswith('.json'):
                    # 移除文件扩展名
                    bank_name = filename[:-5]
                    banks.append(bank_name)
            return sorted(banks)
        except Exception:
            return []
    
    def load_document(self, filename: str) -> List[Dict]:
        """加载技术规范文档"""
        file_path = os.path.join(self.raw_file_dir, filename)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_question_bank_by_name(self, bank_name_without_ext: str) -> List[Dict]:
        """根据题库名称加载题库文件"""
        bank_path = os.path.join(self.question_dataset_dir, f"{bank_name_without_ext}.json")
        if os.path.exists(bank_path):
            with open(bank_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _is_similar_question(self, new_question: Dict, existing_questions: List[Dict], threshold: int = 80) -> bool:
        """
        检查新生成的题目是否与现有题目相似。
        使用模糊匹配 (fuzz.ratio) 来判断相似度。
        threshold: 相似度阈值 (0-100)。
        """
        new_q_text = new_question['question'].strip()
        new_q_type = new_question['type']

        for existing_q in existing_questions:
            existing_q_text = existing_q['question'].strip()
            existing_q_type = existing_q['type']

            # 类型不同直接跳过，或者你也可以根据需要调整逻辑
            if new_q_type != existing_q_type:
                continue

            # 使用模糊匹配检查问题文本的相似度
            similarity = fuzz.ratio(new_q_text, existing_q_text)
            if similarity >= threshold:
                # 可以进一步检查选项（如果需要），但问题文本相似通常足够
                if new_q_type == 'single_choice' and 'options' in new_question and 'options' in existing_q:
                    # 简单检查选项数量和部分选项内容，防止完全不同但问题相似的情况
                    # 这里可以根据需要细化，例如比较所有选项的集合相似度
                    if len(new_question['options']) == len(existing_q['options']):
                        # 检查至少一个选项是否高度相似
                        option_similarity_found = False
                        for new_opt in new_question['options']:
                            for existing_opt in existing_q['options']:
                                if fuzz.ratio(new_opt, existing_opt) >= threshold:
                                    option_similarity_found = True
                                    break
                            if option_similarity_found:
                                break
                        if option_similarity_found:
                            print(f"检测到相似题目 (相似度: {similarity}%):")
                            print(f"  新题: {new_q_text}")
                            print(f"  旧题: {existing_q_text}")
                            return True
                else: # 判断题或单选题仅基于问题文本相似度
                    print(f"检测到相似题目 (相似度: {similarity}%):")
                    print(f"  新题: {new_q_text}")
                    print(f"  旧题: {existing_q_text}")
                    return True
        return False
    
    def generate_questions(self, filename: str, count: int) -> List[Dict]:
        """生成题目"""
        try:
            document = self.load_document(filename)
            if not document:
                print(f"文档 {filename} 为空或加载失败。")
                return []

            # 获取现有题库，用于查重
            base_name = os.path.splitext(filename)[0]
            existing_questions = self.load_question_bank_by_name(f"{base_name}题库")
            print(f"加载现有题库 {base_name}题库.json，共 {len(existing_questions)} 道题目用于查重。")
            
            questions = []
            attempt_count = 0 # 尝试生成题目的次数
            max_attempts_per_question = 5 # 每道题最多尝试次数
            max_total_attempts = count * max_attempts_per_question # 总尝试次数上限

            # 为了避免无限循环，即使文档很大，也只从其中随机选择足够多的片段
            # selected_items = random.sample(document, min(count * 2, len(document))) # 之前的方法，现在可能需要更多样本来确保多样性

            while len(questions) < count and attempt_count < max_total_attempts:
                # 随机选择文档片段，确保每次都有机会选择新的片段
                item = random.choice(document) if document else None
                if not item:
                    break # 如果文档为空，则停止

                question_type = random.choice(['single_choice', 'judge'])
                new_question = None

                if question_type == 'single_choice':
                    new_question = self._generate_single_choice_question(item, document)
                else:
                    new_question = self._generate_judge_question(item)
                
                attempt_count += 1

                if new_question:
                    # 检查新生成的题目是否与现有或已生成的题目相似
                    if not self._is_similar_question(new_question, questions + existing_questions):
                        new_question['idx'] = len(questions) + 1 # 重新编排序号
                        new_question['source_file'] = filename
                        questions.append(new_question)
                    else:
                        print(f"跳过相似题目: {new_question.get('question', '未知问题')[:30]}...") # 打印提示
                
            print(f"生成了 {len(questions)} 道不重复题目。总尝试次数: {attempt_count}")
            return questions
        except Exception as e:
            print(f"生成题目时出错: {e}")
            return []
    
    def _generate_single_choice_question(self, item: Dict, document: List[Dict]) -> Optional[Dict]:
        """生成单选题"""
        try:
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
            
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        question_data = json.loads(json_str)
                        # 验证大模型输出的JSON格式是否正确
                        if all(k in question_data for k in ['question', 'options', 'answer']):
                            return {
                                'type': 'single_choice',
                                'question': question_data['question'],
                                'options': question_data['options'],
                                'answer': question_data['answer']
                            }
                except json.JSONDecodeError:
                    pass
                
                return self._parse_simple_single_choice(content, item)
            
            return None
        except Exception as e:
            print(f"生成单选题时出错: {e}")
            return self._generate_fallback_single_choice(item)
    
    def _generate_judge_question(self, item: Dict) -> Optional[Dict]:
        """生成判断题"""
        try:
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
            
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        question_data = json.loads(json_str)
                        # 验证大模型输出的JSON格式是否正确
                        if all(k in question_data for k in ['question', 'answer']):
                            return {
                                'type': 'judge',
                                'question': question_data['question'],
                                'answer': question_data['answer']
                            }
                except json.JSONDecodeError:
                    pass
                
                return self._parse_simple_judge(content, item)
            
            return None
        except Exception as e:
            print(f"生成判断题时出错: {e}")
            return self._generate_fallback_judge(item)
    
    def _parse_simple_single_choice(self, content: str, item: Dict) -> Dict:
        """简单解析单选题内容（备用）"""
        return {
            'type': 'single_choice',
            'question': f"关于{item['title']}，以下哪个说法是正确的？",
            'options': ["A. 选项A", "B. 选项B", "C. 选项C"],
            'answer': "A"
        }
    
    def _parse_simple_judge(self, content: str, item: Dict) -> Dict:
        """简单解析判断题内容（备用）"""
        return {
            'type': 'judge',
            'question': f"关于{item['title']}的描述是否正确？",
            'answer': "正确"
        }
    
    def _generate_fallback_single_choice(self, item: Dict) -> Dict:
        """生成备用单选题"""
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
    
    def _generate_fallback_judge(self, item: Dict) -> Dict:
        """生成备用判断题"""
        return {
            'type': 'judge',
            'question': f"{item['title']}的相关要求是明确规定的。",
            'answer': "正确"
        }
    
    def save_question_bank(self, source_filename: str, new_questions: List[Dict]) -> str:
        """
        保存题库。如果同名题库已存在，则合并新旧题目并去重。
        """
        base_name = os.path.splitext(source_filename)[0]
        question_filename = f"{base_name}题库.json"
        question_path = os.path.join(self.question_dataset_dir, question_filename)
        
        all_questions = []
        if os.path.exists(question_path):
            # 加载现有题库
            with open(question_path, 'r', encoding='utf-8') as f:
                try:
                    all_questions = json.load(f)
                    print(f"检测到现有题库 {question_filename}，包含 {len(all_questions)} 道题目。")
                except json.JSONDecodeError:
                    print(f"警告: 题库 {question_filename} 格式损坏，将创建新题库。")
                    all_questions = []

        # 合并新旧题目
        # 使用一个集合来存储已经处理过的问题文本，用于快速查重（完全重复的）
        seen_questions_text = set(q['question'] for q in all_questions)
        
        # 记录新增的题目数量
        added_count = 0

        for q in new_questions:
            # 这里的查重是针对完全重复的，更高级的模糊查重在 _is_similar_question 中实现
            if q['question'] not in seen_questions_text:
                all_questions.append(q)
                seen_questions_text.add(q['question'])
                added_count += 1
            else:
                print(f"跳过已存在题目 (完全重复): {q['question'][:30]}...")

        # 重新为所有题目编排 idx，确保其连续性
        for i, q in enumerate(all_questions):
            q['idx'] = i + 1
        
        # 保存合并后的题库
        with open(question_path, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)
        
        print(f"已向 {question_filename} 添加 {added_count} 道新题目。")
        print(f"题库最终包含 {len(all_questions)} 道题目。")
        return question_filename
    
    def load_questions_for_quiz(self, bank_name: str, count: int) -> List[Dict]:
        """加载题目用于答题"""
        try:
            bank_path = os.path.join(self.question_dataset_dir, f"{bank_name}.json")
            
            with open(bank_path, 'r', encoding='utf-8') as f:
                all_questions = json.load(f)
            
            # 随机选择题目
            selected_questions = random.sample(all_questions, min(count, len(all_questions)))
            
            return selected_questions
        except Exception as e:
            print(f"加载题目时出错: {e}")
            return []
    
    def check_answer(self, question: Dict, user_answer: str) -> bool:
        """检查答案是否正确"""
        try:
            correct_answer = question['answer'].lower().strip()
            user_answer = user_answer.lower().strip()
            
            if question['type'] == 'single_choice':
                # 单选题：检查字母答案或完整选项
                # 正确答案可能是 'A', 'B', 'C'
                # 用户答案可能是 'A', 'B', 'C' 或 'A. 选项内容'
                
                # 1. 直接比较用户答案是否与正确答案字母相同
                if user_answer == correct_answer.lower():
                    return True
                            
                # 2. 如果用户输入的是完整选项，尝试匹配
                if 'options' in question:
                    for option in question['options']:
                        if option.lower().strip() == user_answer:
                            # 提取选项字母，与正确答案的字母比较
                            option_letter_match = re.match(r'([A-D])\.', option, re.IGNORECASE)
                            if option_letter_match and option_letter_match.group(1).lower() == correct_answer.lower():
                                return True
                
                return False
            
            elif question['type'] == 'judge':
                # 判断题：支持多种答案格式
                positive_answers = ['正确', '对', '是', 'true', 'yes', '√']
                negative_answers = ['错误', '不对', '否', 'false', 'no', '×']
                
                if correct_answer in positive_answers:
                    return user_answer in positive_answers
                elif correct_answer in negative_answers:
                    return user_answer in negative_answers
                else:
                    # 如果正确答案不是标准格式，则进行严格匹配
                    return user_answer == correct_answer
            
            return False
        except Exception:
            return False