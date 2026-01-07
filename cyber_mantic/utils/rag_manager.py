"""
RAG (Retrieval-Augmented Generation) 管理器

功能：
- 文档索引：将文档分块并建立索引
- 检索：基于关键词检索相关文档片段
- 问答：结合检索结果生成回答

设计参考：docs/design/02_典籍模块设计.md
"""
import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import Counter

from utils.logger import get_logger


@dataclass
class DocumentChunk:
    """文档片段"""
    chunk_id: str
    document_path: str
    document_title: str
    content: str
    position: int  # 片段在文档中的位置
    category: Optional[str] = None


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk: DocumentChunk
    score: float
    matched_terms: List[str]


class RAGManager:
    """
    RAG管理器

    提供文档索引、检索、问答功能
    使用简单的TF-IDF变体进行关键词检索
    """

    def __init__(self, index_dir: Optional[Path] = None):
        self.logger = get_logger(__name__)

        # 索引存储目录
        if index_dir is None:
            index_dir = Path.home() / ".cyber_mantic" / "rag_index"
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # 索引文件路径
        self._chunks_file = self.index_dir / "chunks.json"
        self._index_file = self.index_dir / "index.json"
        self._meta_file = self.index_dir / "meta.json"

        # 内存中的数据
        self._chunks: Dict[str, DocumentChunk] = {}
        self._inverted_index: Dict[str, List[str]] = {}  # term -> [chunk_ids]
        self._doc_hashes: Dict[str, str] = {}  # path -> content_hash

        # 中文停用词
        self._stop_words = set([
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
            "一", "个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
            "着", "没有", "看", "好", "自己", "这", "那", "他", "她", "它",
            "们", "什么", "为", "与", "或", "及", "等", "如", "被", "把"
        ])

        # 加载已有索引
        self._load_index()

    def _load_index(self):
        """加载已有索引"""
        try:
            # 加载元数据
            if self._meta_file.exists():
                with open(self._meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    self._doc_hashes = meta.get('doc_hashes', {})

            # 加载文档片段
            if self._chunks_file.exists():
                with open(self._chunks_file, 'r', encoding='utf-8') as f:
                    chunks_data = json.load(f)
                    for chunk_dict in chunks_data:
                        chunk = DocumentChunk(**chunk_dict)
                        self._chunks[chunk.chunk_id] = chunk

            # 加载倒排索引
            if self._index_file.exists():
                with open(self._index_file, 'r', encoding='utf-8') as f:
                    self._inverted_index = json.load(f)

            self.logger.info(f"已加载RAG索引：{len(self._chunks)} 个片段")
        except Exception as e:
            self.logger.warning(f"加载RAG索引失败: {e}")

    def _save_index(self):
        """保存索引到磁盘"""
        try:
            # 保存元数据
            with open(self._meta_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'doc_hashes': self._doc_hashes,
                    'updated_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            # 保存文档片段
            with open(self._chunks_file, 'w', encoding='utf-8') as f:
                chunks_data = [asdict(c) for c in self._chunks.values()]
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)

            # 保存倒排索引
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(self._inverted_index, f, ensure_ascii=False)

            self.logger.debug("RAG索引已保存")
        except Exception as e:
            self.logger.error(f"保存RAG索引失败: {e}")

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _tokenize(self, text: str) -> List[str]:
        """
        中文分词（简单实现）

        使用正则表达式分割，支持中文字符和英文单词
        """
        # 移除标点符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)

        # 分割：中文单字 + 英文单词
        tokens = []

        # 匹配英文单词和数字
        for match in re.finditer(r'[a-zA-Z0-9]+', text):
            word = match.group().lower()
            if len(word) > 1:
                tokens.append(word)

        # 中文：按字分词（简单实现）
        # 实际生产中应使用jieba等分词库
        chinese_text = re.findall(r'[\u4e00-\u9fff]+', text)
        for segment in chinese_text:
            # 生成2-gram和3-gram
            for i in range(len(segment)):
                # 单字
                if segment[i] not in self._stop_words:
                    tokens.append(segment[i])
                # 2-gram
                if i + 1 < len(segment):
                    bigram = segment[i:i+2]
                    tokens.append(bigram)
                # 3-gram
                if i + 2 < len(segment):
                    trigram = segment[i:i+3]
                    tokens.append(trigram)

        return tokens

    def _chunk_document(self, content: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        将文档分割成片段

        Args:
            content: 文档内容
            chunk_size: 每个片段的大致字符数
            overlap: 片段之间的重叠字符数
        """
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', content)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # 保留重叠部分
                    if overlap > 0 and len(current_chunk) > overlap:
                        current_chunk = current_chunk[-overlap:]
                    else:
                        current_chunk = ""
                current_chunk += para + "\n\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # 如果没有分段，按字符数强制分割
        if not chunks and content:
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk.strip())

        return chunks if chunks else [content[:chunk_size]] if content else []

    def index_document(self, file_path: str, category: Optional[str] = None) -> int:
        """
        索引单个文档

        Args:
            file_path: 文档路径
            category: 文档分类

        Returns:
            int: 新增的片段数量
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.warning(f"文档不存在: {file_path}")
            return 0

        # 读取内容
        try:
            if path.suffix.lower() in ('.md', '.txt'):
                content = path.read_text(encoding='utf-8')
            else:
                self.logger.info(f"跳过不支持的格式: {path.suffix}")
                return 0
        except Exception as e:
            self.logger.warning(f"读取文档失败 {file_path}: {e}")
            return 0

        # 检查是否需要更新
        content_hash = self._compute_hash(content)
        if self._doc_hashes.get(file_path) == content_hash:
            return 0  # 内容未变化

        # 删除旧的片段
        self._remove_document(file_path)

        # 分割文档
        chunks = self._chunk_document(content)

        # 创建片段并索引
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{content_hash}_{i}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_path=file_path,
                document_title=path.stem,
                content=chunk_text,
                position=i,
                category=category
            )
            self._chunks[chunk_id] = chunk

            # 更新倒排索引
            tokens = self._tokenize(chunk_text)
            for token in set(tokens):  # 去重
                if token not in self._inverted_index:
                    self._inverted_index[token] = []
                if chunk_id not in self._inverted_index[token]:
                    self._inverted_index[token].append(chunk_id)

        # 记录文档哈希
        self._doc_hashes[file_path] = content_hash

        return len(chunks)

    def _remove_document(self, file_path: str):
        """移除文档的所有片段"""
        # 找到该文档的所有片段
        chunk_ids_to_remove = [
            chunk_id for chunk_id, chunk in self._chunks.items()
            if chunk.document_path == file_path
        ]

        # 从倒排索引中移除
        for chunk_id in chunk_ids_to_remove:
            for term, chunk_list in self._inverted_index.items():
                if chunk_id in chunk_list:
                    chunk_list.remove(chunk_id)

        # 从片段字典中移除
        for chunk_id in chunk_ids_to_remove:
            del self._chunks[chunk_id]

        # 移除文档哈希
        if file_path in self._doc_hashes:
            del self._doc_hashes[file_path]

    def index_directory(self, dir_path: str, category: Optional[str] = None) -> int:
        """
        索引整个目录

        Args:
            dir_path: 目录路径
            category: 分类名称

        Returns:
            int: 新增的片段总数
        """
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            return 0

        total_chunks = 0
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ('.md', '.txt'):
                chunks = self.index_document(str(file_path), category=category or file_path.parent.name)
                total_chunks += chunks

        self._save_index()
        self.logger.info(f"目录索引完成: {dir_path}, 新增 {total_chunks} 个片段")
        return total_chunks

    def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[RetrievalResult]:
        """
        检索相关文档片段

        Args:
            query: 查询文本
            top_k: 返回结果数量
            category: 限定分类

        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        # 分词
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 统计每个片段的匹配得分
        chunk_scores: Dict[str, Tuple[float, List[str]]] = {}

        for token in query_tokens:
            if token in self._inverted_index:
                for chunk_id in self._inverted_index[token]:
                    chunk = self._chunks.get(chunk_id)
                    if chunk is None:
                        continue

                    # 分类过滤
                    if category and chunk.category != category:
                        continue

                    if chunk_id not in chunk_scores:
                        chunk_scores[chunk_id] = (0.0, [])

                    score, matched = chunk_scores[chunk_id]
                    # TF-IDF 变体：词频 / 文档频率
                    tf = chunk.content.lower().count(token.lower())
                    df = len(self._inverted_index.get(token, []))
                    idf = 1.0 / (1.0 + df) if df > 0 else 1.0
                    chunk_scores[chunk_id] = (score + tf * idf, matched + [token])

        # 排序并返回
        results = []
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1][0], reverse=True)

        for chunk_id, (score, matched) in sorted_chunks[:top_k]:
            chunk = self._chunks.get(chunk_id)
            if chunk:
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=score,
                    matched_terms=list(set(matched))
                ))

        return results

    def answer_question(self, question: str, api_manager, top_k: int = 3) -> Tuple[str, List[RetrievalResult]]:
        """
        基于检索结果回答问题

        Args:
            question: 用户问题
            api_manager: AI API管理器
            top_k: 检索结果数量

        Returns:
            Tuple[str, List[RetrievalResult]]: (回答, 引用来源)
        """
        # 检索相关内容
        results = self.search(question, top_k=top_k)

        if not results:
            return "抱歉，未能在典籍中找到相关内容。请尝试更换关键词或直接阅读相关文档。", []

        # 构建上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"【来源{i}：{result.chunk.document_title}】\n{result.chunk.content}")

        context = "\n\n---\n\n".join(context_parts)

        # 构建提示词
        prompt = f"""你是一位术数典籍专家。请根据以下参考资料回答用户的问题。

## 参考资料

{context}

---

## 用户问题

{question}

---

## 回答要求

1. 基于参考资料回答，不要编造内容
2. 如果参考资料不足以回答问题，请诚实说明
3. 引用资料时注明来源
4. 语言简洁清晰，重点突出
5. 如有专业术语，简要解释
"""

        # 调用AI生成回答
        try:
            answer = api_manager.analyze(prompt)
            return answer, results
        except Exception as e:
            self.logger.error(f"AI回答生成失败: {e}")
            return f"生成回答时出错：{e}", results

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            'total_chunks': len(self._chunks),
            'total_documents': len(self._doc_hashes),
            'total_terms': len(self._inverted_index),
            'categories': list(set(c.category for c in self._chunks.values() if c.category))
        }

    def clear_index(self):
        """清空索引"""
        self._chunks.clear()
        self._inverted_index.clear()
        self._doc_hashes.clear()
        self._save_index()
        self.logger.info("RAG索引已清空")


# 全局RAG管理器实例
_rag_manager: Optional[RAGManager] = None


def get_rag_manager() -> RAGManager:
    """获取全局RAG管理器实例"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager()
    return _rag_manager
