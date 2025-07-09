import os
import sys

# Add project root to Python path
# This ensures that imports like 'backend.main' work correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import json
import time
# Import the refactored QuestionSystemBackend from backend.main
from backend.main import QuestionSystemBackend

# Page configuration for Streamlit app
st.set_page_config(
    page_title="本地知识库自动出题系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the backend using Streamlit's cache_resource to avoid re-initialization
@st.cache_resource
def get_backend():
    return QuestionSystemBackend()

backend = get_backend()

# Main title of the application
st.title("📚 本地知识库自动出题系统")
st.markdown("---")

# Store the current page selection in session state to detect page changes
if 'current_page_selection' not in st.session_state:
    st.session_state.current_page_selection = "📁 选择上传技术文档"

# Sidebar navigation for different functionalities
st.sidebar.title("功能导航")
new_page_selection = st.sidebar.radio(
    "选择功能",
    ["📁 选择上传技术文档", "🎯 开始出题", "✏️ 立即答题"],
    key="main_navigation" # Add a key to ensure callback triggers on selection
)

# Detect if the page has switched
if new_page_selection != st.session_state.current_page_selection:
    # If page switched, reset all quiz-related session states
    for key in ['quiz_questions', 'current_question', 'user_answers', 'quiz_started', 'quiz_completed']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.current_page_selection = new_page_selection
    # Rerun immediately to ensure state is cleared for the new page
    st.rerun()

# Update the current page variable
page = new_page_selection

# Page 1: Upload Technical Document
if page == "📁 选择上传技术文档":
    st.header("📁 上传技术规范文档")

    uploaded_file = st.file_uploader(
        "选择JSON格式的技术规范文件",
        type=['json'],
        help="请上传符合规定格式的JSON文件"
    )

    if uploaded_file is not None:
        try:
            # Read file content
            file_content = json.load(uploaded_file)

            # Validate file format using the backend method
            if backend.validate_json_format(file_content):
                # Save the file using the backend method
                file_path = backend.save_uploaded_file(uploaded_file)
                st.success(f"✅ 文件上传成功！已保存为: {file_path}")

                # Display file preview
                st.subheader("📄 文件内容预览")
                with st.expander("查看文件内容"):
                    st.json(file_content[:3])  # Display first 3 entries
                    if len(file_content) > 3:
                        st.info(f"文件共包含 {len(file_content)} 个条目")
            else:
                st.error("❌ 文件格式不符合要求，请检查JSON格式")

        except json.JSONDecodeError:
            st.error("❌ 文件格式错误，请上传有效的JSON文件")
        except Exception as e:
            st.error(f"❌ 处理文件时出错: {str(e)}")

# Page 2: Start Question Generation
elif page == "🎯 开始出题":
    st.header("🎯 智能题目生成")

    # Get list of uploaded files using the backend method
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
                # Display generation progress
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    status_text.text("正在分析文档内容...")
                    progress_bar.progress(25)

                    # Generate questions using the backend method
                    questions = backend.generate_questions(selected_file, question_count)

                    status_text.text("正在生成题目...")
                    progress_bar.progress(75)

                    if questions:
                        # Save question bank using the backend method
                        question_file = backend.save_question_bank(selected_file, questions)
                        progress_bar.progress(100)

                        status_text.text("✅ 题目生成完成！")
                        st.success(f"🎉 成功生成 {len(questions)} 道题目！")
                        st.info(f"📝 题库已保存为: {question_file}")

                        # Display question preview
                        st.subheader("📋 题目预览")
                        with st.expander("查看生成的题目"):
                            for i, q in enumerate(questions[:min(len(questions), 3)], 1): # Show max 3 questions
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
                    # Clear progress bar and status text
                    progress_bar.empty()
                    status_text.empty()

# Page 3: Start Quiz
elif page == "✏️ 立即答题":
    st.header("✏️ 开始答题")

    # Get available question banks using the backend method
    question_banks = backend.get_question_banks()

    if not question_banks:
        st.warning("⚠️ 暂无可用题库，请先生成题目")
        if st.button("🎯 前往生成题目"):
            st.session_state.current_page_selection = "🎯 开始出题"
            st.rerun()
    else:
        # If quiz not started and not completed, show selection interface
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
                # Initialize quiz state
                questions = backend.load_questions_for_quiz(selected_bank, answer_count)
                if questions:
                    st.session_state.quiz_questions = questions
                    st.session_state.current_question = 0
                    st.session_state.user_answers = []
                    st.session_state.quiz_started = True
                    st.session_state.quiz_completed = False # Ensure set to incomplete when starting
                    st.rerun() # Rerun to enter quiz flow
                else:
                    st.error("无法加载题目，请检查题库或选择数量。")

        # Quiz interface
        if st.session_state.get('quiz_started', False) and not st.session_state.get('quiz_completed', False):
            questions = st.session_state.quiz_questions
            current_idx = st.session_state.current_question

            if current_idx < len(questions):
                question = questions[current_idx]

                st.subheader(f"问题 {current_idx + 1}/{len(questions)}")
                st.markdown(f"**{question['question']}**")

                # Use a unique key for input widgets to ensure content resets on rerun
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
                elif question['type'] == 'subjective': # New input for subjective questions
                    user_input = st.text_area(
                        "请输入你的答案:",
                        height=150,
                        key=user_answer_key
                    )
                else:
                    user_input = None # Fallback

                # Save user input to session state to access after button click
                st.session_state.current_user_input = user_input

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("提交答案", key=f"submit_btn_{current_idx}"):
                        user_answer = st.session_state.current_user_input
                        if user_answer is not None and user_answer.strip() != "": # Ensure answer is not empty for subjective
                            # Check answer using the backend method
                            is_correct = backend.check_answer(question, user_answer)
                            st.session_state.user_answers.append({
                                'question': question,
                                'user_answer': user_answer,
                                'is_correct': is_correct
                            })

                            # Display feedback
                            if is_correct:
                                st.success("✅ 回答正确！")
                            else:
                                st.error(f"❌ 回答错误，正确答案是: {question['answer']}")

                            # Move to next question or complete quiz
                            if current_idx < len(questions) - 1:
                                time.sleep(1) # Small delay for user to see feedback
                                st.session_state.current_question += 1
                                st.rerun()
                            else:
                                # Quiz completed
                                st.session_state.quiz_completed = True
                                st.session_state.quiz_started = False # Stop displaying questions
                                st.rerun() # Rerun to display results
                        else:
                            st.warning("请先选择或输入答案")

                with col2:
                    if st.button("结束答题", key=f"end_quiz_btn_{current_idx}"):
                        st.session_state.quiz_completed = True
                        st.session_state.quiz_started = False # Stop displaying questions
                        st.rerun()
            else: # If current_idx == len(questions), all questions answered
                st.session_state.quiz_completed = True
                st.session_state.quiz_started = False # Stop displaying questions
                st.rerun() # Force rerun to display results

        # Display quiz results (if quiz_completed is True and on the quiz page)
        if st.session_state.get('quiz_completed', False):
            st.success("🎉 答题完成！")

            # Calculate results
            total_questions = len(st.session_state.user_answers)
            correct_count = sum(1 for ans in st.session_state.user_answers if ans['is_correct'])
            accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0

            # Display scores
            st.subheader("📊 答题结果")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("总题数", total_questions)
            with col2:
                st.metric("正确数", correct_count)
            with col3:
                st.metric("正确率", f"{accuracy:.1f}%")

            # Learning suggestions
            if accuracy < 60:
                st.error("📚 建议重新学习相关技术规范内容")
            elif accuracy < 80:
                st.warning("📖 建议针对错题部分加强学习")
            else:
                st.success("🎊 掌握情况良好，继续保持！")

            # Wrong answer analysis
            wrong_answers = [ans for ans in st.session_state.user_answers if not ans['is_correct']]
            if wrong_answers:
                st.subheader("❌ 错题分析")
                with st.expander("查看错题详情"):
                    for i, ans in enumerate(wrong_answers, 1):
                        st.markdown(f"**错题 {i}**")
                        st.markdown(f"问题: {ans['question']['question']}")
                        st.markdown(f"你的答案: {ans['user_answer']}")
                        correct_answer_display = ans['question']['answer']
                        if ans['question']['type'] == 'single_choice' and 'options' in ans['question']:
                            # Find the full option text for single choice questions
                            for option in ans['question']['options']:
                                if option.lower().startswith(correct_answer_display.lower() + "."):
                                    correct_answer_display = option
                                    break
                        st.markdown(f"正确答案: {correct_answer_display}")
                        st.markdown("---")

            # Retake quiz button
            if st.button("🔄 重新答题"):
                # Clear all quiz-related session states for a new quiz round
                for key in ['quiz_questions', 'current_question', 'user_answers', 'quiz_started', 'quiz_completed', 'current_user_input']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

# Footer information
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>📚 本地知识库自动出题系统 | 基于大语言模型智能生成题目</p>
    </div>
    """,
    unsafe_allow_html=True
)
