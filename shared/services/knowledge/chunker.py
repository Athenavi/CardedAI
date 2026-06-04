"""
文档切片器

将长文本切分为适合向量化和检索的小片段。

支持三种切片策略：
- recursive: 递归字符切片（默认，按分隔符层级递归分割）
- semantic: 语义切片（按段落/章节结构分割）
- sentence: 句子级切片（按句子边界分割）
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from src.unified_logger import default_logger as logger


@dataclass
class ChunkResult:
    """切片结果"""
    content: str
    chunk_index: int
    metadata: Dict = field(default_factory=dict)
    token_count: int = 0


class DocumentChunker:
    """
    文档切片器

    将长文本切分为固定大小的片段，支持重叠和多种策略。
    """

    # 分隔符优先级（从高到低）
    SEPARATORS = [
        "\n\n\n",   # 章节分隔
        "\n\n",     # 段落分隔
        "\n",       # 行分隔
        "。",       # 中文句号
        ".",        # 英文句号
        "！",       # 中文感叹号
        "？",       # 中文问号
        "!",        # 英文感叹号
        "?",        # 英文问号
        "；",       # 中文分号
        ";",        # 英文分号
        "，",       # 中文逗号
        ",",        # 英文逗号
        " ",        # 空格
    ]

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        初始化切片器

        Args:
            chunk_size: 目标切片大小（字符数）
            chunk_overlap: 切片重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def chunk(
        self,
        text: str,
        strategy: str = "recursive",
        chunk_size: int = None,
        chunk_overlap: int = None,
        metadata: Dict = None,
    ) -> List[ChunkResult]:
        """
        对文本进行切片

        Args:
            text: 待切片的文本
            strategy: 切片策略 (recursive/semantic/sentence)
            chunk_size: 切片大小（覆盖默认值）
            chunk_overlap: 重叠大小（覆盖默认值）
            metadata: 附加到每个切片的元数据

        Returns:
            切片结果列表
        """
        if not text or not text.strip():
            return []

        size = chunk_size or self.chunk_size
        overlap = chunk_overlap or self.chunk_overlap
        meta = metadata or {}

        text = text.strip()

        if strategy == "recursive":
            chunks = self._recursive_split(text, size, overlap)
        elif strategy == "semantic":
            chunks = self._semantic_split(text, size, overlap)
        elif strategy == "sentence":
            chunks = self._sentence_split(text, size, overlap)
        else:
            logger.warning(f"未知切片策略 '{strategy}'，使用 recursive")
            chunks = self._recursive_split(text, size, overlap)

        results = []
        for i, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
            token_count = self._estimate_tokens(chunk_text)
            results.append(ChunkResult(
                content=chunk_text.strip(),
                chunk_index=i,
                metadata={**meta, "strategy": strategy},
                token_count=token_count,
            ))

        return results

    def _recursive_split(self, text: str, size: int, overlap: int) -> List[str]:
        """
        递归字符切片

        按分隔符优先级逐级分割，直到每个片段不超过目标大小。
        """
        if len(text) <= size:
            return [text]

        # 找到合适的分隔符
        for separator in self.SEPARATORS:
            if separator not in text:
                continue

            splits = text.split(separator)
            if len(splits) <= 1:
                continue

            # 合并小片段
            chunks = []
            current = ""

            for split in splits:
                piece = split if not current else separator + split

                if not current:
                    current = split
                elif len(current) + len(piece) <= size:
                    current += piece
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    current = split

            if current.strip():
                chunks.append(current.strip())

            # 如果产生了有效分割，处理重叠
            if len(chunks) > 1:
                return self._add_overlap(chunks, overlap)

            # 如果单个片段仍然太大，尝试更小的分隔符递归
            result = []
            for chunk in chunks:
                if len(chunk) > size:
                    result.extend(self._recursive_split(chunk, size, overlap))
                else:
                    result.append(chunk)
            return result

        # 所有分隔符都不行，硬切
        return self._hard_split(text, size, overlap)

    def _semantic_split(self, text: str, size: int, overlap: int) -> List[str]:
        """
        语义切片

        按段落和章节结构分割，尽量保持语义完整性。
        """
        # 按章节分隔（Markdown 标题）
        sections = re.split(r"(?=\n#{1,6}\s)", text)

        if len(sections) > 1:
            chunks = []
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                if len(section) <= size:
                    chunks.append(section)
                else:
                    # 章节内部按段落切分
                    paragraphs = section.split("\n\n")
                    current = ""
                    for para in paragraphs:
                        if not current:
                            current = para
                        elif len(current) + len(para) + 2 <= size:
                            current += "\n\n" + para
                        else:
                            chunks.append(current.strip())
                            current = para
                    if current.strip():
                        chunks.append(current.strip())
            return self._add_overlap(chunks, overlap)

        # 没有标题结构，按段落分割
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            chunks = []
            current = ""
            for para in paragraphs:
                if not current:
                    current = para
                elif len(current) + len(para) + 2 <= size:
                    current += "\n\n" + para
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    # 如果单个段落太大，回退到递归切分
                    if len(para) > size:
                        chunks.extend(self._recursive_split(para, size, overlap))
                    else:
                        current = para
                        continue
                    current = ""
            if current.strip():
                chunks.append(current.strip())
            return self._add_overlap(chunks, overlap)

        # 回退到递归切分
        return self._recursive_split(text, size, overlap)

    def _sentence_split(self, text: str, size: int, overlap: int) -> List[str]:
        """
        句子级切片

        按句子边界分割，每个片段包含一个或多个完整句子。
        """
        # 中英文句子边界
        sentences = re.split(r"(?<=[。！？.!?；;])\s*", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return [text]

        chunks = []
        current = ""

        for sentence in sentences:
            if not current:
                current = sentence
            elif len(current) + len(sentence) + 1 <= size:
                current += " " + sentence
            else:
                if current.strip():
                    chunks.append(current.strip())
                # 单个句子太大，回退到递归切分
                if len(sentence) > size:
                    chunks.extend(self._recursive_split(sentence, size, overlap))
                    current = ""
                else:
                    current = sentence

        if current.strip():
            chunks.append(current.strip())

        return self._add_overlap(chunks, overlap)

    def _hard_split(self, text: str, size: int, overlap: int) -> List[str]:
        """硬切（按字符数强制分割）"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start = end - overlap if overlap < size else end
        return chunks

    def _add_overlap(self, chunks: List[str], overlap: int) -> List[str]:
        """为切片添加重叠"""
        if overlap <= 0 or len(chunks) <= 1:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            # 取前一个片段的末尾作为重叠前缀
            overlap_text = prev[-overlap:] if len(prev) > overlap else prev
            # 找到重叠文本的自然断点
            for sep in ["\n", "。", ".", " ", "，", ","]:
                idx = overlap_text.find(sep)
                if idx > 0:
                    overlap_text = overlap_text[idx + 1:]
                    break
            result.append(overlap_text + chunks[i])

        return result

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        估算 Token 数量

        简单启发式：中文每字约 1.5 token，英文每词约 1 token。
        """
        # 分离中英文
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # 英文单词数（去除中文后的空白分割）
        no_chinese = re.sub(r"[\u4e00-\u9fff]", " ", text)
        english_words = len(no_chinese.split())
        return int(chinese_chars * 1.5 + english_words)

    def get_supported_strategies(self) -> List[str]:
        """获取支持的切片策略"""
        return ["recursive", "semantic", "sentence"]


# 全局单例
document_chunker = DocumentChunker()
