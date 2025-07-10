import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add project root to Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.agents.question_agent import QuestionAgent
from backend.components.llm_connector import LLMConnector
from backend.components.data_loader import DataLoader

# Mock data for testing
MOCK_DOCUMENT_CONTENT = [
    {"idx": "6.3", "title": "指示灯", "text": "电能表使用高亮、长寿命LED 作为指示灯，各指示灯的布置位置参照附录中电能表外观简图，并要求如下： a） 脉冲指示灯。红色，平时灭，计量有功电能时闪烁； b） 跳闸指示灯。黄色，负荷开关分断时亮，平时灭。"},
    {"idx": "6.4", "title": "停电显示", "text": "a） 停电后，液晶显示自动关闭； b） 液晶显示关闭后，可用按键方式唤醒液晶显示；为节省电池，不支持红外唤醒，唤醒后如无操作，自动循环显示一遍后关闭显示；按键显示操作结束30 秒后关闭显示。"},
    {"idx": "7.1", "title": "外观结构、安装尺寸图及颜色", "text": "a） 电能表外形尺寸有两种规格： 1） 规格1：160mm（高）×112mm（宽）×58mm（厚），适用于远程不带通信模块的单相费控电能表； 2） 规格2：160mm（高）×112mm（宽）×71mm（厚），适用于其他类型的单相费控电能表。"},
    {"idx": "8.1", "title": "采样元件", "text": "a） 采样元件如采用精密互感器，应保证精密互感器具有足够的准确度，并用硬连接可靠地固定在端子上，或采用焊接方式固定在线路板上；不应使用胶类物质或捆扎方式固定。 b） 采样元件如采用锰铜分流器，锰铜片与铜支架应焊接良好、可靠，不应采用铆接工艺；锰铜分流器与其采样连接端子之间应采用电子束或钎焊。"}
]

MOCK_EXISTING_QUESTIONS = [
    {"type": "judge", "question": "根据技术规范，表座可以使用回收材料制作。", "answer": "错误", "idx": 1, "source_file": "单相智能电能表形式规范.json"},
    {"type": "subjective", "question": "根据技术规范，电能表的封印及封印螺钉在材料、处理方式和功能设计上有哪些具体要求？请详细说明。", "answer": "封印螺钉应采用HPb59－1铜或铁，并经过钝化、镀锌、镀铬或镀镍等防锈处理；螺钉需进行防脱落处理，尺寸应符合附录H规定。封印结构应防止未授权人打开表盖触及内部部件，电能表应具有出厂封印和检定封，其中出厂封为一次性编码封印，且在安装运行状态下封印状态应可在正面直接观察到。表盖封印右耳为出厂封，左耳为检定封。", "idx": 2, "source_file": "单相智能电能表形式规范.json"},
    {"type": "single_choice", "question": "根据技术规范，关于铭牌的要求以下哪项是正确的？", "options": ["A. 铭牌材料应具有防紫外线功能，但无需具备耐高温性能", "B. 铭牌必须带有条形码，且条形码应为白底黑字", "C. 铭牌上不需要标注计量器具生产许可证标识"], "answer": "B", "idx": 3, "source_file": "单相智能电能表形式规范.json"}
]


# ... (之前的导入和 MOCK_DATA 不变) ...

def run_question_agent_tests():
    """
    Demonstrates the interface and functionality of the QuestionAgent class.
    Mocks LLMConnector and DataLoader for isolated testing.
    """
    print("--- Testing QuestionAgent ---")

    # Mock LLMConnector and DataLoader
    mock_llm_connector = MagicMock(spec=LLMConnector)
    mock_data_loader = MagicMock(spec=DataLoader)

    # Configure mock_data_loader behavior
    mock_data_loader.load_document.return_value = MOCK_DOCUMENT_CONTENT
    mock_data_loader.load_question_bank_by_name.return_value = MOCK_EXISTING_QUESTIONS
    mock_data_loader.save_question_bank.side_effect = lambda filename, questions: f"mock_path/question_dataset/{filename}"

    # Configure mock_llm_connector behavior for question generation
    # 提供模拟的LLM原始JSON字符串
    mock_llm_raw_responses = [
        json.dumps({"question": "指示灯中，红色脉冲指示灯的用途是什么？", "options": ["A. 表示电能表故障", "B. 计量有功电能时闪烁", "C. 负荷开关分断时亮"], "answer": "B"}),
        json.dumps({"question": "停电后，电能表液晶显示可通过红外唤醒。", "answer": "错误"}),
        json.dumps({"question": "请阐述电能表外形尺寸的两种规格及其适用范围。", "answer": "电能表外形尺寸有两种规格：规格1为160mm×112mm×58mm，适用于远程不带通信模块的单相费控电能表；规格2为160mm×112mm×71mm，适用于其他类型的单相费控电能表。"}),
        json.dumps({"question": "关于采样元件的固定方式，以下哪种是不允许的？", "options": ["A. 硬连接固定在端子上", "B. 焊接方式固定在线路板上", "C. 胶类物质或捆扎方式固定"], "answer": "C"}),
        json.dumps({"question": "线路板表面应清洗干净，不得有明显的污渍和焊迹，且无需做绝缘处理。", "answer": "错误"}),
        json.dumps({"question": "请描述电能表线路板的材料和工艺要求。", "answer": "线路板须用耐氧化、耐腐蚀的双面/多层敷铜环氧树脂板，并具有电能表生产厂家的标识。表面应清洗干净，不得有明显的污渍和焊迹，应做绝缘、防腐处理。所有元器件均能防锈蚀、防氧化，紧固点牢靠。电子元器件（除电源器件外）宜使用贴片元件，使用表面贴装工艺生产。焊接应采用回流焊、波峰焊工艺。"})
    ]
    mock_llm_connector.generate_text.side_effect = mock_llm_raw_responses

    # 关键修改：直接模拟 parse_..._json 方法返回带有 'type' 的完整字典，
    # 模拟其真实行为，即它们会添加 'type' 字段。
    mock_llm_connector.parse_single_choice_json.side_effect = lambda content: {
        'type': 'single_choice', **json.loads(content)} if content else None
    mock_llm_connector.parse_judge_json.side_effect = lambda content: {
        'type': 'judge', **json.loads(content)} if content else None
    mock_llm_connector.parse_subjective_json.side_effect = lambda content: {
        'type': 'subjective', **json.loads(content)} if content else None

    # Initialize QuestionAgent
    question_agent = QuestionAgent(mock_llm_connector, mock_data_loader)

    # ... (Test Case 1 和 Test Case 2 保持不变) ...

    print("\n--- QuestionAgent tests completed ---")

if __name__ == "__main__":
    run_question_agent_tests()
