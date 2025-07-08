# PDF转JSON工具 - 改进版本
# 这个工具不包含在主项目中，仅用于数据预处理

import os
import json
import re
from typing import List, Dict, Optional
import fitz  # PyMuPDF
from dotenv import load_dotenv
import dashscope
from dashscope import Generation

class PDFToJSONConverter:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('BAILIAN_API_KEY')
        dashscope.api_key = self.api_key
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF中提取文本内容"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"PDF文本提取失败: {e}")
            return ""
    
    def call_llm(self, prompt: str, max_tokens: int = 3000) -> str:
        """调用阿里百炼大模型API"""
        try:
            response = Generation.call(
                model='qwen-max',
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.1,  # 进一步降低温度以获得更稳定的输出
                top_p=0.8
            )
            
            if response.status_code == 200:
                return response.output.text
            else:
                return f"API调用失败: {response.message}"
        except Exception as e:
            return f"API调用异常: {str(e)}"
    
    def split_text_into_chunks(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """将长文本分割成较小的块"""
        # 首先尝试按章节编号分割
        # 匹配类似 4.3.1、4.3.2 这样的编号
        section_pattern = r'(\d+\.\d+(?:\.\d+)*)\s+'
        sections = re.split(section_pattern, text)
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        i = 0
        while i < len(sections):
            section = sections[i]
            
            # 如果这是一个章节编号
            if re.match(r'^\d+\.\d+(?:\.\d+)*$', section.strip()):
                # 获取对应的内容
                content = sections[i + 1] if i + 1 < len(sections) else ""
                full_section = section + " " + content
                
                if current_size + len(full_section) > max_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = full_section
                    current_size = len(full_section)
                else:
                    current_chunk += full_section
                    current_size += len(full_section)
                
                i += 2  # 跳过内容部分
            else:
                # 普通内容，添加到当前块
                if current_size + len(section) > max_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = section
                    current_size = len(section)
                else:
                    current_chunk += section
                    current_size += len(section)
                i += 1
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # 如果没有找到章节，使用原来的分割方法
        if len(chunks) <= 1:
            chunks = self.split_by_paragraphs(text, max_chunk_size)
        
        return chunks
    
    def split_by_paragraphs(self, text: str, max_chunk_size: int) -> List[str]:
        """按段落分割文本"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) < max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_structured_content(self, text_chunk: str) -> List[Dict]:
        """使用LLM提取结构化内容"""
        prompt = f"""
你是一个专门处理技术规范文档的专家。请从以下文档片段中提取章节信息，并严格按照JSON格式输出。

文档内容：
{text_chunk}

任务要求：
1. 识别文档中的章节编号（如4.3.1、4.3.2、4.4.1等）
2. 提取每个章节的标题
3. 提取每个章节的完整内容

输出要求：
- 必须输出有效的JSON数组，不能有任何其他文字
- 每个章节对象包含三个字段：idx（章节编号）、title（标题）、text（内容）
- 如果没有明确的章节编号，请根据内容逻辑推断
- 保持原文内容的完整性，包括字母编号（a）、b）、c）等）

示例输出格式：
[
    {{
        "idx": "4.3.1",
        "title": "外观结构",
        "text": "a） 具有正向、反向有功电能量计量功能。 b） 具有分时计量功能；有功电能量应对尖、峰、平、谷等各时段电能量及总电能量分别进行累计、存储。"
    }},
    {{
        "idx": "4.3.2",
        "title": "时钟功能",
        "text": "a） 应具有日历、计时、闰年自动转换功能。 b） 时钟端子输出频率为1Hz。"
    }}
]

请严格按照上述JSON格式输出，不要添加任何解释或其他文字：
"""
        
        response = self.call_llm(prompt, max_tokens=3000)
        print(f"LLM原始响应: {response[:200]}...")  # 打印前200个字符用于调试
        
        # 多种方式尝试解析JSON
        json_data = self.parse_json_response(response)
        
        if json_data:
            print(f"成功解析到 {len(json_data)} 个章节")
            return json_data
        else:
            print("JSON解析失败，尝试备用方法...")
            return self.extract_sections_by_regex(text_chunk)
    
    def parse_json_response(self, response: str) -> List[Dict]:
        """尝试多种方法解析JSON响应"""
        # 方法1：寻找JSON数组
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            try:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            except:
                pass
        
        # 方法2：寻找JSON对象数组（可能有多个独立的对象）
        json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response)
        if json_objects:
            try:
                parsed_objects = []
                for obj_str in json_objects:
                    obj = json.loads(obj_str)
                    parsed_objects.append(obj)
                return parsed_objects
            except:
                pass
        
        # 方法3：清理响应中的多余字符
        try:
            cleaned_response = re.sub(r'```json\s*|\s*```', '', response)
            cleaned_response = re.sub(r'^[^\[]*\[', '[', cleaned_response)
            cleaned_response = re.sub(r'\][^\]]*$', ']', cleaned_response)
            return json.loads(cleaned_response)
        except:
            pass
        
        return []
    
    def extract_sections_by_regex(self, text: str) -> List[Dict]:
        """使用正则表达式作为备用方法提取章节"""
        print("使用正则表达式提取章节...")
        
        # 匹配章节编号模式
        section_pattern = r'(\d+\.\d+(?:\.\d+)*)\s+([^\n]+?)(?=\n|$)(.*?)(?=\d+\.\d+(?:\.\d+)*\s+|$)'
        matches = re.findall(section_pattern, text, re.DOTALL)
        
        sections = []
        for match in matches:
            idx = match[0].strip()
            title = match[1].strip()
            content = match[2].strip()
            
            if idx and (title or content):
                sections.append({
                    "idx": idx,
                    "title": title if title else "未命名章节",
                    "text": content if content else title
                })
        
        # 如果没有找到标准格式，尝试更宽松的匹配
        if not sections:
            # 按段落分割，寻找包含编号的段落
            paragraphs = text.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if re.search(r'\d+\.\d+', paragraph):
                    sections.append({
                        "idx": f"section_{i+1}",
                        "title": "提取的章节",
                        "text": paragraph.strip()
                    })
        
        return sections
    
    def merge_and_clean_sections(self, all_sections: List[Dict]) -> List[Dict]:
        """合并和清理章节数据"""
        # 去重和合并逻辑
        seen_idx = set()
        cleaned_sections = []
        
        for section in all_sections:
            idx = section.get('idx', '')
            title = section.get('title', '')
            text = section.get('text', '')
            
            # 基本验证
            if not idx or not text:
                continue
            
            # 去重
            if idx in seen_idx:
                continue
            
            seen_idx.add(idx)
            
            # 清理内容
            cleaned_section = {
                "idx": idx.strip(),
                "title": title.strip(),
                "text": text.strip()
            }
            
            cleaned_sections.append(cleaned_section)
        
        return cleaned_sections
    
    def convert_pdf_to_json(self, pdf_path: str, output_path: str) -> bool:
        """将PDF转换为JSON格式"""
        print(f"开始处理PDF文件: {pdf_path}")
        
        # 提取PDF文本
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print("PDF文本提取失败")
            return False
        
        print(f"提取的文本长度: {len(text)} 字符")
        
        # 分割文本
        chunks = self.split_text_into_chunks(text)
        print(f"文本分割为 {len(chunks)} 个块")
        
        # 处理每个文本块
        all_sections = []
        for i, chunk in enumerate(chunks):
            print(f"正在处理第 {i+1}/{len(chunks)} 个文本块...")
            print(f"块内容预览: {chunk[:100]}...")
            
            sections = self.extract_structured_content(chunk)
            if sections:
                all_sections.extend(sections)
                print(f"从第 {i+1} 个块提取到 {len(sections)} 个章节")
            else:
                print(f"第 {i+1} 个块未提取到有效章节")
        
        # 合并和清理
        final_sections = self.merge_and_clean_sections(all_sections)
        print(f"最终提取到 {len(final_sections)} 个章节")
        
        # 保存JSON文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_sections, f, ensure_ascii=False, indent=2)
            print(f"成功保存到: {output_path}")
            return True
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
            return False
    
    def debug_text_structure(self, text: str):
        """调试文本结构"""
        print("=== 文本结构调试 ===")
        print(f"总长度: {len(text)}")
        
        # 查找章节编号
        section_numbers = re.findall(r'\d+\.\d+(?:\.\d+)*', text)
        print(f"找到的章节编号: {section_numbers}")
        
        # 显示前500个字符
        print(f"前500个字符: {text[:500]}")
        
        # 按行分割，显示包含数字的行
        lines = text.split('\n')
        numbered_lines = [line for line in lines if re.search(r'\d+\.\d+', line)]
        print(f"包含章节编号的行数: {len(numbered_lines)}")
        for i, line in enumerate(numbered_lines[:10]):  # 显示前10行
            print(f"  {i+1}: {line}")


def main():
    """主函数 - 使用示例"""
    converter = PDFToJSONConverter()
    
    # 示例使用
    pdf_file = "单相静止式多费率电能表技术规范.pdf"
    json_file = "单相静止式多费率电能表技术规范.json"
    
    if os.path.exists(pdf_file):
        # 调试模式：先分析文本结构
        text = converter.extract_text_from_pdf(pdf_file)
        if text:
            converter.debug_text_structure(text)
        
        # 执行转换
        success = converter.convert_pdf_to_json(pdf_file, json_file)
        if success:
            print("✅ PDF转JSON转换完成！")
            
            # 验证生成的JSON文件
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"生成的JSON包含 {len(data)} 个章节")
                    
                    # 显示所有章节的示例
                    print("\n提取的章节:")
                    for i, section in enumerate(data):
                        print(f"{i+1}. {section.get('idx', '')} - {section.get('title', '')}")
                        print(f"   内容: {section.get('text', '')[:100]}...")
                        print()
            except Exception as e:
                print(f"验证JSON文件失败: {e}")
        else:
            print("❌ PDF转JSON转换失败")
    else:
        print(f"PDF文件不存在: {pdf_file}")


if __name__ == "__main__":
    main()