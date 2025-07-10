import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add project root to Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.components.data_loader import DataLoader

# Define mock data paths for testing
MOCK_BASE_DATA_DIR = os.path.join(project_root, 'test_data_loader_temp')
MOCK_RAW_FILE_DIR = os.path.join(MOCK_BASE_DATA_DIR, 'raw_files')
MOCK_QUESTION_DATASET_DIR = os.path.join(MOCK_BASE_DATA_DIR, 'question_dataset')

def setup_mock_dirs():
    """Create mock directories for testing."""
    os.makedirs(MOCK_RAW_FILE_DIR, exist_ok=True)
    os.makedirs(MOCK_QUESTION_DATASET_DIR, exist_ok=True)

def cleanup_mock_dirs():
    """Clean up mock directories after testing."""
    import shutil
    if os.path.exists(MOCK_BASE_DATA_DIR):
        shutil.rmtree(MOCK_BASE_DATA_DIR)

def run_data_loader_tests():
    """
    Demonstrates the interface and functionality of the DataLoader class.
    """
    print("--- Testing DataLoader ---")

    cleanup_mock_dirs() # Ensure clean state
    setup_mock_dirs()

    # 在patch之前保存原始的os.path.join引用
    _original_os_path_join = os.path.join

    with patch('os.path.join', side_effect=lambda base, *args:
               # 在这里使用保存的原始os.path.join引用，而不是被patch后的os.path.join
               _original_os_path_join(MOCK_BASE_DATA_DIR, *args) if base == 'data' else _original_os_path_join(base, *args)), \
         patch('os.makedirs', return_value=None) as mock_makedirs, \
         patch('os.listdir', side_effect=lambda path: 
                # 模拟 os.listdir 以便 get_uploaded_files 和 get_question_banks 能找到文件
                ['test_doc.json'] if path == MOCK_RAW_FILE_DIR else
                ['test_bank.json'] if path == MOCK_QUESTION_DATASET_DIR else
                []
            ): # 模拟makedirs避免实际创建
        
        data_loader = DataLoader()

        # 确保目录被尝试创建（通过mock_makedirs验证）
        mock_makedirs.assert_any_call(MOCK_RAW_FILE_DIR, exist_ok=True)
        mock_makedirs.assert_any_call(MOCK_QUESTION_DATASET_DIR, exist_ok=True)

        # Test Case 1: validate_json_format
        print("\n--- Test 1: validate_json_format ---")
        valid_json_data = [
            {"idx": "1.1", "title": "Title 1", "text": "Text 1"},
            {"idx": "1.2", "title": "Title 2", "text": "Text 2"}
        ]
        invalid_json_data = [{"idx": "1.1", "title": "Title 1"}] # Missing 'text'
        print(f"Input (Valid): {valid_json_data[0]}")
        is_valid = data_loader.validate_json_format(valid_json_data)
        print(f"Output (Valid): {is_valid}") # Expected: True
        print(f"Input (Invalid): {invalid_json_data[0]}")
        is_invalid = data_loader.validate_json_format(invalid_json_data)
        print(f"Output (Invalid): {is_invalid}") # Expected: False

        # Test Case 2: save_uploaded_file and get_uploaded_files
        print("\n--- Test 2: save_uploaded_file and get_uploaded_files ---")
        mock_uploaded_file = MagicMock()
        mock_uploaded_file.name = "test_doc.json"
        mock_uploaded_file.getvalue.return_value = json.dumps(valid_json_data, ensure_ascii=False).encode('utf-8')
        
        # 模拟文件写入操作
        with patch('builtins.open', MagicMock()) as mock_open:
            print(f"Input (save_uploaded_file): uploaded_file.name='{mock_uploaded_file.name}'")
            saved_path = data_loader.save_uploaded_file(mock_uploaded_file)
            print(f"Output (save_uploaded_file): Saved to '{saved_path}'")
            mock_open.assert_called_once_with(_original_os_path_join(MOCK_RAW_FILE_DIR, "test_doc.json"), 'wb') # 使用原始的join

        uploaded_files = data_loader.get_uploaded_files()
        print(f"Output (get_uploaded_files): {uploaded_files}") # Expected: ['test_doc.json']

        # Test Case 3: load_document
        print("\n--- Test 3: load_document ---")
        # 模拟文件读取操作
        with patch('builtins.open', MagicMock(
            return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=json.dumps(valid_json_data))
            )), __exit__=MagicMock())
        )), \
        patch('os.path.exists', return_value=True): # 模拟文件存在
            doc_content = data_loader.load_document("test_doc.json")
            print(f"Input (load_document): 'test_doc.json'")
            print(f"Output (load_document): {doc_content[:1]}...") # Expected: content of test_doc.json
            assert doc_content == valid_json_data

        # Test Case 4: save_question_bank and get_question_banks
        print("\n--- Test 4: save_question_bank and get_question_banks ---")
        mock_questions = [
            {"type": "single_choice", "question": "Q1", "options": ["A", "B"], "answer": "A", "idx": 1, "source_file": "test_doc.json"},
            {"type": "judge", "question": "Q2", "answer": "正确", "idx": 2, "source_file": "test_doc.json"},
            {"type": "subjective", "question": "Q3", "answer": "Answer for Q3", "idx": 3, "source_file": "test_doc.json"}
        ]
        question_bank_name = "test_bank.json"
        
        # 模拟题库文件写入
        with patch('builtins.open', MagicMock()) as mock_open:
            print(f"Input (save_question_bank): '{question_bank_name}', {len(mock_questions)} questions")
            saved_bank_path = data_loader.save_question_bank(question_bank_name, mock_questions)
            print(f"Output (save_question_bank): Saved to '{saved_bank_path}'")
            mock_open.assert_called_once_with(_original_os_path_join(MOCK_QUESTION_DATASET_DIR, question_bank_name), 'w', encoding='utf-8') # 使用原始的join

        question_banks = data_loader.get_question_banks()
        print(f"Output (get_question_banks): {question_banks}") # Expected: ['test_bank']

        # Test Case 5: load_question_bank_by_name
        print("\n--- Test 5: load_question_bank_by_name ---")
        # 模拟题库文件读取
        with patch('builtins.open', MagicMock(
            return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=json.dumps(mock_questions))
            )), __exit__=MagicMock())
        )), \
        patch('os.path.exists', return_value=True): # 模拟文件存在
            loaded_bank = data_loader.load_question_bank_by_name("test_bank")
            print(f"Input (load_question_bank_by_name): 'test_bank'")
            print(f"Output (load_question_bank_by_name): {loaded_bank[:1]}...") # Expected: content of test_bank.json
            assert loaded_bank == mock_questions

        # Test Case 6: load_questions_for_quiz
        print("\n--- Test 6: load_questions_for_quiz ---")
        # 模拟题库文件读取
        with patch('builtins.open', MagicMock(
            return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(
                read=MagicMock(return_value=json.dumps(mock_questions))
            )), __exit__=MagicMock())
        )), \
        patch('os.path.exists', return_value=True): # 模拟文件存在
            quiz_questions = data_loader.load_questions_for_quiz("test_bank", 2)
            print(f"Input (load_questions_for_quiz): 'test_bank', count=2")
            print(f"Output (load_questions_for_quiz): {len(quiz_questions)} questions loaded") # Expected: 2 questions
            assert len(quiz_questions) == 2

    cleanup_mock_dirs()
    print("\n--- DataLoader tests completed ---")

if __name__ == "__main__":
    run_data_loader_tests()
