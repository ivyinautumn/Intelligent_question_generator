import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import json
import time
from backend.main import QuestionSystemBackend

# 页面配置
st.set_page_config(
    page_title="本地知识库自动出题系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化后端
@st.cache_resource
def get_backend():
    return QuestionSystemBackend()

backend = get_backend()

# 主标题
st.title("📚 本地知识库自动出题系统")
st.markdown("---")

# 在会话状态中存储当前页面的选择，用于检测页面切换
if 'current_page_selection' not in st.session_state:
    st.session_state.current_page_selection = "📁 选择上传技术文档"

# 侧边栏导航
st.sidebar.title("功能导航")
new_page_selection = st.sidebar.radio(
    "选择功能",
    ["📁 选择上传技术文档", "🎯 开始出题", "✏️ 立即答题"],
    key="main_navigation" # 添加key，确保每次选择都触发回调
)

# 检测页面是否切换
if new_page_selection != st.session_state.current_page_selection:
    # 页面切换时，重置所有与答题相关的 session state
    for key in ['quiz_questions', 'current_question', 'user_answers', 'quiz_started', 'quiz_completed']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.current_page_selection = new_page_selection
    # 在页面切换时，立即重新运行以确保状态被清除
    st.rerun()

# 更新当前页面
page = new_page_selection

# 页面1: 上传技术文档
if page == "📁 选择上传技术文档":
    st.header("📁 上传技术规范文档")
    
    uploaded_file = st.file_uploader(
        "选择JSON格式的技术规范文件",
        type=['json'],
        help="请上传符合规定格式的JSON文件"
    )
    
    if uploaded_file is not None:
        try:
            # 读取文件内容
            file_content = json.load(uploaded_file)
            
            # 验证文件格式
            if backend.validate_json_format(file_content):
                # 保存文件
                file_path = backend.save_uploaded_file(uploaded_file)
                st.success(f"✅ 文件上传成功！已保存为: {file_path}")
                
                # 显示文件预览
                st.subheader("📄 文件内容预览")
                with st.expander("查看文件内容"):
                    st.json(file_content[:3])  # 显示前3个条目
                    if len(file_content) > 3:
                        st.info(f"文件共包含 {len(file_content)} 个条目")
            else:
                st.error("❌ 文件格式不符合要求，请检查JSON格式")
                
        except json.JSONDecodeError:
            st.error("❌ 文件格式错误，请上传有效的JSON文件")
        except Exception as e:
            st.error(f"❌ 处理文件时出错: {str(e)}")

# 页面2: 开始出题
elif page == "🎯 开始出题":
    st.header("🎯 智能题目生成")
    
    # 获取已上传的文件列表
    uploaded_files = backend.get_uploaded_files()
    
    if not uploaded_files:
        st.warning("⚠️ 暂无已上传的技术文档，请先上传文档")
        if st.button("📁 前往上传页面"):
            st.session_state.current_page_selection = "📁 选择上传技术文档"
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_file = st.selectbox(
                "选择技术文档",
                uploaded_files,
                help="选择要生成题目的技术规范文档"
            )
        
        with col2:
            question_count = st.selectbox(
                "选择出题数量",
                [5, 10, 20],
                help="选择要生成的题目数量"
            )
        
        if st.button("🚀 开始生成题目", type="primary"):
            if selected_file and question_count:
                # 显示生成进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # 生成题目
                    status_text.text("正在分析文档内容...")
                    progress_bar.progress(25)
                    
                    questions = backend.generate_questions(selected_file, question_count)
                    
                    status_text.text("正在生成题目...")
                    progress_bar.progress(75)
                    
                    if questions:
                        # 保存题库
                        question_file = backend.save_question_bank(selected_file, questions)
                        progress_bar.progress(100)
                        
                        status_text.text("✅ 题目生成完成！")
                        st.success(f"🎉 成功生成 {len(questions)} 道题目！")
                        st.info(f"📝 题库已保存为: {question_file}")
                        
                        # 显示题目预览
                        st.subheader("📋 题目预览")
                        with st.expander("查看生成的题目"):
                            for i, q in enumerate(questions[:min(len(questions), 3)], 1): # 最多显示前3个
                                st.markdown(f"**题目 {i}**")
                                st.markdown(f"类型: {q['type']}")
                                st.markdown(f"问题: {q['question']}")
                                if q['type'] == 'single_choice':
                                    st.markdown(f"选项: {q['options']}")
                                st.markdown(f"答案: {q['answer']}")
                                st.markdown("---")
                    else:
                        st.error("❌ 题目生成失败，请检查文档内容")
                        
                except Exception as e:
                    st.error(f"❌ 生成过程中出错: {str(e)}")
                
                finally:
                    # 清除进度条和状态文本
                    progress_bar.empty()
                    status_text.empty()

# 页面3: 立即答题
elif page == "✏️ 立即答题":
    st.header("✏️ 开始答题")
    
    # 获取可用的题库
    question_banks = backend.get_question_banks()
    
    if not question_banks:
        st.warning("⚠️ 暂无可用题库，请先生成题目")
        if st.button("🎯 前往生成题目"):
            st.session_state.current_page_selection = "🎯 开始出题"
            st.rerun()
    else:
        # 如果答题未开始且未完成，显示选择题库和数量的界面
        if not st.session_state.get('quiz_started', False) and not st.session_state.get('quiz_completed', False):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_bank = st.selectbox(
                    "选择题库",
                    question_banks,
                    help="选择要答题的题库",
                    key="select_quiz_bank"
                )
            
            with col2:
                answer_count = st.selectbox(
                    "选择答题数量",
                    [5, 10, 20],
                    help="选择要答题的数量",
                    key="select_quiz_count"
                )
            
            if st.button("📝 开始答题", type="primary", key="start_quiz_button"):
                # 初始化答题状态
                questions = backend.load_questions_for_quiz(selected_bank, answer_count)
                if questions:
                    st.session_state.quiz_questions = questions
                    st.session_state.current_question = 0
                    st.session_state.user_answers = []
                    st.session_state.quiz_started = True
                    st.session_state.quiz_completed = False # 确保开始答题时设置为未完成
                    st.rerun() # 重新运行以进入答题流程
                else:
                    st.error("无法加载题目，请检查题库或选择数量。")

        # 答题界面
        if st.session_state.get('quiz_started', False) and not st.session_state.get('quiz_completed', False):
            questions = st.session_state.quiz_questions
            current_idx = st.session_state.current_question
            
            if current_idx < len(questions):
                question = questions[current_idx]
                
                st.subheader(f"问题 {current_idx + 1}/{len(questions)}")
                st.markdown(f"**{question['question']}**")
                
                # 为确保每次刷新时输入框内容被重置，使用一个空的 `st.empty()` 作为占位符
                # 或者更简单的方式是每次渲染时确保 key 改变
                user_answer_key = f"q_{current_idx}_{st.session_state.get('rerun_count', 0)}"

                if question['type'] == 'single_choice':
                    options = question['options']
                    user_input = st.radio(
                        "请选择答案:",
                        options,
                        key=user_answer_key
                    )
                elif question['type'] == 'judge':
                    user_input = st.text_input(
                        "请输入答案 (如: 正确/错误、是/否等):",
                        key=user_answer_key
                    )
                else:
                    user_input = None # Fallback

                # 保存用户输入到 session state，以便在提交按钮后访问
                st.session_state.current_user_input = user_input

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("提交答案", key=f"submit_btn_{current_idx}"):
                        # 从 session_state 获取用户输入
                        user_answer = st.session_state.current_user_input
                        if user_answer is not None:
                            # 检查答案
                            is_correct = backend.check_answer(question, user_answer)
                            st.session_state.user_answers.append({
                                'question': question,
                                'user_answer': user_answer,
                                'is_correct': is_correct
                            })
                            
                            # 显示答案反馈
                            if is_correct:
                                st.success("✅ 回答正确！")
                            else:
                                st.error(f"❌ 回答错误，正确答案是: {question['answer']}")
                            
                            # 下一题
                            if current_idx < len(questions) - 1:
                                time.sleep(1) # 稍微延迟，让用户看到反馈
                                st.session_state.current_question += 1
                                st.rerun()
                            else:
                                # 答题完成
                                st.session_state.quiz_completed = True
                                # 答题完成后，清除当前题目显示区域，避免内容残留
                                st.session_state.quiz_started = False # 设置为False，不再显示题目
                                st.rerun() # 重新运行以显示结果
                        else:
                            st.warning("请先选择或输入答案")
                
                with col2:
                    if st.button("结束答题", key=f"end_quiz_btn_{current_idx}"):
                        st.session_state.quiz_completed = True
                        st.session_state.quiz_started = False # 结束答题时也设置 False
                        st.rerun()
            else: # 当 current_idx == len(questions) 时，说明题目已答完
                st.session_state.quiz_completed = True
                st.session_state.quiz_started = False # 不再显示题目
                st.rerun() # 强制重新运行以显示结果

        # 显示答题结果 (无论是否是刚完成，只要 quiz_completed 为 True 且在答题页面就显示)
        if st.session_state.get('quiz_completed', False):
            # 只有在quiz_completed为True时才显示结果
            st.success("🎉 答题完成！")
            
            # 统计结果
            total_questions = len(st.session_state.user_answers)
            correct_count = sum(1 for ans in st.session_state.user_answers if ans['is_correct'])
            accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            # 显示成绩
            st.subheader("📊 答题结果")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("总题数", total_questions)
            with col2:
                st.metric("正确数", correct_count)
            with col3:
                st.metric("正确率", f"{accuracy:.1f}%")
            
            # 学习建议
            if accuracy < 60:
                st.error("📚 建议重新学习相关技术规范内容")
            elif accuracy < 80:
                st.warning("📖 建议针对错题部分加强学习")
            else:
                st.success("🎊 掌握情况良好，继续保持！")
            
            # 错题分析
            wrong_answers = [ans for ans in st.session_state.user_answers if not ans['is_correct']]
            if wrong_answers:
                st.subheader("❌ 错题分析")
                with st.expander("查看错题详情"):
                    for i, ans in enumerate(wrong_answers, 1):
                        st.markdown(f"**错题 {i}**")
                        st.markdown(f"问题: {ans['question']['question']}")
                        st.markdown(f"你的答案: {ans['user_answer']}")
                        st.markdown(f"正确答案: {ans['question']['answer']}")
                        st.markdown("---")
            
            # 重新答题按钮
            if st.button("🔄 重新答题"):
                # 彻底清除所有答题状态，准备新一轮答题
                for key in ['quiz_questions', 'current_question', 'user_answers', 'quiz_started', 'quiz_completed', 'current_user_input']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

# 页面底部信息
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>📚 本地知识库自动出题系统 | 基于大语言模型智能生成题目</p>
    </div>
    """,
    unsafe_allow_html=True
)