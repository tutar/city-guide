import re
from typing import List


class SentenceSplitterService:
    def __init__(self):
        pass

    def should_skip_citation(self, text: str) -> bool:
        """
        判断是否应该跳过citation

        条件：
        1. 是单行（没有回车符）
        2. 以特殊字符串开头（"---"、"####"等）

        返回：
        - True: 应该跳过
        - False: 不应该跳过
        """
        if not text or not text.strip():
            return True

        # 检查是否是单行（没有换行符）
        if "\n" in text:
            return False

        # 去除首尾空白
        cleaned_text = text.strip()

        # 检查是否以特殊字符串开头
        skip_prefixes = [
            "---",
            "***",
            "___",  # 分割线
            "####",
            "###",
            "##",
            "#",  # 标题
            "```",  # 代码块标记
            "<!--",  # HTML注释
            "|",  # 表格行
            "![",  # 图片
        ]

        for prefix in skip_prefixes:
            if cleaned_text.startswith(prefix):
                return True

        # 额外的检查：纯分割线（只有---、***等）
        if re.match(r"^[\-\*_]{3,}\s*$", cleaned_text):
            return True

        return False

    def split_markdown_by_paragraphs(self, markdown_text: str) -> List[str]:
        """
        简单的按段落分割Markdown文本
        保留所有原始格式，包括URL和Markdown标记
        """
        # 按空行分割段落（\n\n或更多换行）
        paragraphs = re.split(r"\n\s*\n", markdown_text.strip())

        # 过滤空段落并去除每段的首尾空白
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para:  # 只保留非空段落
                cleaned_paragraphs.append(para)

        return cleaned_paragraphs

    def split_with_basic_processing(self, markdown_text: str) -> List[str]:
        """
        带基础处理的段落分割：
        - 保留所有原始内容
        - 处理代码块
        - 处理分割线
        """
        lines = markdown_text.split("\n")
        paragraphs = []
        current_paragraph = []
        in_code_block = False

        for line in lines:
            line = line.rstrip()  # 只去除右侧空白，保留左侧缩进

            # 检测代码块
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                # 代码块边界也作为段落分隔
                if current_paragraph:
                    paragraphs.append("\n".join(current_paragraph))
                    current_paragraph = []
                # 代码块标记本身作为一个段落
                if line.strip():
                    paragraphs.append(line)
                continue

            # 在代码块中，直接逐行保留
            if in_code_block:
                paragraphs.append(line)
                continue

            # 检测分割线
            if re.match(r"^[\-\*_]{3,}\s*$", line.strip()):
                if current_paragraph:
                    paragraphs.append("\n".join(current_paragraph))
                    current_paragraph = []
                paragraphs.append(line)  # 分割线作为独立段落
                continue

            # 空行表示段落结束
            if not line.strip():
                if current_paragraph:
                    paragraphs.append("\n".join(current_paragraph))
                    current_paragraph = []
                continue

            # 普通行，添加到当前段落
            current_paragraph.append(line)

        # 处理最后一个段落
        if current_paragraph:
            paragraphs.append("\n".join(current_paragraph))

        return paragraphs


# 使用示例
if __name__ == "__main__":
    markdown_content = """
### 港澳通行证办理指南

港澳通行证（全称《往来港澳通行证》）是中国内地居民前往香港、澳门特别行政区的旅行证件。以下是深圳市办理港澳通行证的详细指南：

---

#### 一、办理条件
- 深圳市户籍居民。
- 在深圳市连续缴纳社保满一年的非深户籍居民（部分人员如深圳高校在读学生等可凭在读证明办理）。
- 其他符合国家规定的人员。

---

#### 二、所需材料
1. **身份证明**：
   - 居民身份证（原件及复印件）。
   - 户口簿（户籍居民需提供，非深户籍通常以身份证和居住证/社保记录为准）。
2. **照片**：
   - 近期免冠白底彩色证件照1张（尺寸33mm×48mm）。
   - 可在办理现场自助拍摄或指定照相馆拍摄。
3. **非深户籍补充材料**：
   - 有效的深圳市居住证（原件及复印件）。
   - 或连续缴纳满一年的深圳社保记录（可通过"粤省事"小程序或社保局官网打印）。
4. **特殊情况**：
   - 未成年人需由监护人陪同，提供监护人身份证及关系证明（如户口簿、出生医学证明）。
   - 国家工作人员需提交单位出具的同意出境证明。

---

#### 三、办理流程
1. **预约**：
   - 通过"深圳公安"微信公众号或广东省公安厅出入境政务服务网（https://gdga.gd.gov.cn/crj/）预约办理时间和地点。
2. **填写申请表**：
   - 在线填写或现场领取《中国公民出入境证件申请表》。
3. **现场办理**：
   - 按预约时间到深圳市任一出入境办证大厅提交材料、采集指纹和签名。
4. **缴费**：
   - 通行证工本费：60元/证；签注费用根据类型另计（如一次有效签注15元）。
   - 支持微信、支付宝或银行卡支付。
5. **领取证件**：
   - 可选择自取或邮寄（邮寄费用到付，约7-10个工作日送达）。
   - 进度可通过"深圳公安"公众号或粤省事小程序查询。
"""

    splitter = SentenceSplitterService()

    print("=== 简单段落分割 ===")
    paragraphs1 = splitter.split_markdown_by_paragraphs(markdown_content)
    for i, para in enumerate(paragraphs1, 1):
        print(f"<{i}>: {para}")

    print("\n\n=== 带基础处理的段落分割 ===")
    paragraphs2 = splitter.split_with_basic_processing(markdown_content)
    for i, para in enumerate(paragraphs2, 1):
        print(f"<{i}>: {para}")
