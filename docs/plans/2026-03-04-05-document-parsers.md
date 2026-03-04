# 文档解析插件实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现可扩展的文档解析插件系统，支持 PDF、Markdown、纯文本等格式

**Architecture:**
- 抽象插件基类定义统一接口
- 各格式实现具体解析器
- 插件管理器动态加载
- 预留 skills 目录供未来扩展

**Tech Stack:** PyPDF2, python-docx, python-pptx, Pillow (OCR)

---

## Task 1: 创建文档解析器基类

**Files:**
- Create: `backend/app/plugins/base.py`
- Create: `backend/app/plugins/__init__.py`

**Step 1: Write failing test for parser base class**

创建 `backend/app/tests/test_parser_base.py`:

```python
import pytest
from app.plugins.base import DocumentParser

def test_parser_interface():
    """测试解析器接口"""
    # DocumentParser 是抽象类，无法实例化
    parser = DocumentParser()
    result = parser.parse("test.txt")
    assert result is not None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
uv run pytest app/tests/test_parser_base.py::test_parser_interface -v
```

Expected: FAIL with "Cannot instantiate abstract class"

**Step 3: Implement parser base class**

创建 `backend/app/plugins/base.py`:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

class DocumentParser(ABC):
    """文档解析器抽象基类"""

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        解析文档，返回纯文本

        Args:
            file_path: 文档路径

        Returns:
            提取的文本内容
        """
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """
        判断是否支持该文件类型

        Args:
            file_extension: 文件扩展名（如 .pdf, .md）

        Returns:
            是否支持
        """
        pass

    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否存在且可读

        Args:
            file_path: 文件路径

        Returns:
            文件是否有效
        """
        path = Path(file_path)
        return path.exists() and path.is_file()
```

创建 `backend/app/plugins/__init__.py`:

```python
from app.plugins.base import DocumentParser
from app.plugins.manager import ParserManager
```

**Step 4: Update test**

修改 `backend/app/tests/test_parser_base.py`:

```python
import pytest
from app.plugins.base import DocumentParser

def test_parser_validate_file():
    """测试文件验证方法"""
    parser = DocumentParser()

    # 测试不存在的文件
    assert parser.validate_file("nonexistent.txt") is False
```

**Step 5: Run tests**

```bash
uv run pytest app/tests/test_parser_base.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/plugins/
git commit -m "feat: 创建文档解析器抽象基类"
```

---

## Task 2: 实现 Markdown 解析器

**Files:**
- Create: `backend/app/plugins/md_parser.py`

**Step 1: Write failing test for Markdown parser**

创建 `backend/app/tests/test_md_parser.py`:

```python
import pytest
import tempfile
import os
from app.plugins.md_parser import MarkdownParser

@pytest.mark.asyncio
async def test_markdown_parser():
    """测试 Markdown 解析器"""
    parser = MarkdownParser()

    # 创建临时 Markdown 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# 测试标题\n\n这是测试内容")
        temp_path = f.name

    try:
        assert parser.supports(".md") is True
        assert parser.supports(".pdf") is False

        text = parser.parse(temp_path)
        assert "测试标题" in text
        assert "这是测试内容" in text
    finally:
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_md_parser.py::test_markdown_parser -v
```

Expected: FAIL with "module 'app.plugins.md_parser' not found"

**Step 3: Implement Markdown parser**

创建 `backend/app/plugins/md_parser.py`:

```python
from app.plugins.base import DocumentParser

class MarkdownParser(DocumentParser):
    """Markdown 文档解析器"""

    def supports(self, file_extension: str) -> bool:
        """支持的文件扩展名"""
        return file_extension.lower() in ['.md', '.markdown']

    def parse(self, file_path: str) -> str:
        """
        解析 Markdown 文件

        Args:
            file_path: Markdown 文件路径

        Returns:
            文本内容
        """
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_metadata(self, file_path: str) -> dict:
        """
        提取 Markdown 元数据（如标题、作者等）

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        content = self.parse(file_path)
        lines = content.split('\n')

        metadata = {}
        for line in lines:
            if line.startswith('# '):
                metadata['title'] = line[2:].strip()
                break
            elif line.startswith('title:'):
                metadata['title'] = line.split(':', 1)[1].strip()

        return metadata
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_md_parser.py::test_markdown_parser -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/plugins/md_parser.py backend/app/tests/test_md_parser.py
git commit -m "feat: 实现 Markdown 解析器"
```

---

## Task 3: 实现 PDF 解析器

**Files:**
- Create: `backend/app/plugins/pdf_parser.py`

**Step 1: Write failing test for PDF parser**

创建 `backend/app/tests/test_pdf_parser.py`:

```python
import pytest
import tempfile
from app.plugins.pdf_parser import PDFParser

# 注意：这个测试需要一个真实的 PDF 文件
# 或者使用 pypdf 创建一个简单的测试 PDF

@pytest.mark.asyncio
async def test_pdf_parser_supports():
    """测试 PDF 解析器支持的格式"""
    parser = PDFParser()
    assert parser.supports(".pdf") is True
    assert parser.supports(".md") is False
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_pdf_parser.py::test_pdf_parser_supports -v
```

Expected: FAIL with "module 'app.plugins.pdf_parser' not found"

**Step 3: Implement PDF parser**

创建 `backend/app/plugins/pdf_parser.py`:

```python
from app.plugins.base import DocumentParser
import pypdf

class PDFParser(DocumentParser):
    """PDF 文档解析器"""

    def supports(self, file_extension: str) -> bool:
        """支持的文件扩展名"""
        return file_extension.lower() == '.pdf'

    def parse(self, file_path: str) -> str:
        """
        解析 PDF 文件

        Args:
            file_path: PDF 文件路径

        Returns:
            提取的文本内容
        """
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                number_of_pages = len(reader.pages)

                for i in range(number_of_pages):
                    page = reader.pages[i]
                    text += page.extract_text() + "\n"

        except Exception as e:
            raise RuntimeError(f"PDF 解析失败: {str(e)}")

        return text

    def extract_metadata(self, file_path: str) -> dict:
        """
        提取 PDF 元数据

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        metadata = {}

        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                info = reader.metadata

                if info:
                    metadata['title'] = info.get('/Title', '')
                    metadata['author'] = info.get('/Author', '')
                    metadata['creator'] = info.get('/Creator', '')
                    metadata['producer'] = info.get('/Producer', '')

                metadata['pages'] = len(reader.pages)

        except Exception as e:
            metadata['error'] = str(e)

        return metadata
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_pdf_parser.py::test_pdf_parser_supports -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/plugins/pdf_parser.py backend/app/tests/test_pdf_parser.py
git commit -m "feat: 实现 PDF 解析器"
```

---

## Task 4: 实现纯文本解析器

**Files:**
- Create: `backend/app/plugins/txt_parser.py`

**Step 1: Write failing test for text parser**

创建 `backend/app/tests/test_txt_parser.py`:

```python
import pytest
import tempfile
import os
from app.plugins.txt_parser import TextParser

@pytest.mark.asyncio
async def test_text_parser():
    """测试纯文本解析器"""
    parser = TextParser()

    # 创建临时文本文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是测试文本内容")
        temp_path = f.name

    try:
        assert parser.supports(".txt") is True
        text = parser.parse(temp_path)
        assert "这是测试文本内容" in text
    finally:
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_txt_parser.py::test_text_parser -v
```

Expected: FAIL with "module 'app.plugins.txt_parser' not found"

**Step 3: Implement text parser**

创建 `backend/app/plugins/txt_parser.py`:

```python
from app.plugins.base import DocumentParser
from typing import List

class TextParser(DocumentParser):
    """纯文本解析器"""

    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.txt', '.log', '.csv', '.json']

    def supports(self, file_extension: str) -> bool:
        """支持的文件扩展名"""
        return file_extension.lower() in self.supported_extensions

    def parse(self, file_path: str) -> str:
        """
        解析纯文本文件

        Args:
            file_path: 文本文件路径

        Returns:
            文本内容
        """
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 尝试不同的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        # 如果所有编码都失败，使用二进制模式读取
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')

    def parse_lines(self, file_path: str) -> List[str]:
        """
        按行解析文本文件

        Args:
            file_path: 文件路径

        Returns:
            文本行列表
        """
        text = self.parse(file_path)
        return text.split('\n')
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_txt_parser.py::test_text_parser -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/plugins/txt_parser.py backend/app/tests/test_txt_parser.py
git commit -m "feat: 实现纯文本解析器"
```

---

## Task 5: 实现插件管理器

**Files:**
- Create: `backend/app/plugins/manager.py`

**Step 1: Write failing test for parser manager**

创建 `backend/app/tests/test_parser_manager.py`:

```python
import pytest
import tempfile
import os
from app.plugins.manager import ParserManager

@pytest.mark.asyncio
async def test_parser_manager():
    """测试插件管理器"""
    manager = ParserManager()

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Test")
        md_path = f.name

    try:
        # 测试获取解析器
        parser = manager.get_parser(md_path)
        assert parser is not None
        assert parser.supports(".md") is True

        # 测试解析
        text = manager.parse_document(md_path)
        assert "Test" in text
    finally:
        os.unlink(md_path)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_parser_manager.py::test_parser_manager -v
```

Expected: FAIL with "module 'app.plugins.manager' not found"

**Step 3: Implement parser manager**

创建 `backend/app/plugins/manager.py`:

```python
from typing import List, Optional
from pathlib import Path
from app.plugins.base import DocumentParser
from app.plugins.md_parser import MarkdownParser
from app.plugins.pdf_parser import PDFParser
from app.plugins.txt_parser import TextParser

class ParserManager:
    """文档解析器管理器"""

    def __init__(self):
        """初始化管理器，注册所有内置解析器"""
        self.parsers: List[DocumentParser] = [
            MarkdownParser(),
            PDFParser(),
            TextParser(),
            # 未来可以在这里添加更多解析器
            # WordParser(),
            # OCRParser(),
            # WebParser(),
        ]

    def register_parser(self, parser: DocumentParser):
        """
        注册新的解析器

        Args:
            parser: 解析器实例
        """
        self.parsers.append(parser)

    def get_parser(self, file_path: str) -> Optional[DocumentParser]:
        """
        根据文件路径获取合适的解析器

        Args:
            file_path: 文件路径

        Returns:
            解析器实例，如果不支持则返回 None
        """
        ext = Path(file_path).suffix

        for parser in self.parsers:
            if parser.supports(ext):
                return parser

        return None

    def parse_document(self, file_path: str) -> str:
        """
        自动选择合适的解析器解析文档

        Args:
            file_path: 文件路径

        Returns:
            提取的文本内容

        Raises:
            ValueError: 如果不支持的文件类型
            FileNotFoundError: 如果文件不存在
        """
        parser = self.get_parser(file_path)

        if not parser:
            ext = Path(file_path).suffix
            raise ValueError(
                f"不支持的文件类型: {ext}. "
                f"支持的类型: .md, .pdf, .txt"
            )

        return parser.parse(file_path)

    def get_supported_formats(self) -> List[str]:
        """
        获取所有支持的文件格式

        Returns:
            文件扩展名列表
        """
        formats = set()
        for parser in self.parsers:
            # 每个解析器可能支持多种格式
            # 这里简化处理，实际可以从解析器获取
            if hasattr(parser, 'supported_extensions'):
                formats.update(parser.supported_extensions)
            else:
                # 根据解析器类名推断
                class_name = parser.__class__.__name__.lower()
                if 'markdown' in class_name or 'md' in class_name:
                    formats.update(['.md', '.markdown'])
                elif 'pdf' in class_name:
                    formats.add('.pdf')
                elif 'text' in class_name or 'txt' in class_name:
                    formats.update(['.txt', '.log', '.csv'])

        return sorted(list(formats))
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_parser_manager.py::test_parser_manager -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/plugins/manager.py backend/app/tests/test_parser_manager.py
git commit -m "feat: 实现文档解析器管理器"
```

---

## Task 6: 创建文档解析 API

**Files:**
- Create: `backend/app/api/documents.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing test for documents API**

创建 `backend/app/tests/test_documents_api.py`:

```python
import pytest
import tempfile
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_parse_document():
    """测试文档解析 API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Document")
            temp_path = f.name

        # 这里应该用文件上传，但简化测试
        # 实际应该用 UploadFile
        response = await ac.post("/api/documents/parse", json={
            "file_path": temp_path
        })
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest app/tests/test_documents_api.py::test_parse_document -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Implement documents API**

创建 `backend/app/api/documents.py`:

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import tempfile
import os
from app.plugins.manager import ParserManager

router = APIRouter(prefix="/api/documents", tags=["documents"])

parser_manager = ParserManager()

@router.post("/parse")
async def parse_document(
    file: UploadFile = File(...)
):
    """
    解析上传的文档

    Args:
        file: 上传的文件

    Returns:
        解析结果
    """
    # 验证文件扩展名
    file_ext = os.path.splitext(file.filename)[1]

    if not parser_manager.get_parser(f"test{file_ext}"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}"
        )

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 解析文档
        text = parser_manager.parse_document(tmp_path)

        return {
            "success": True,
            "filename": file.filename,
            "text": text,
            "length": len(text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.get("/formats")
async def get_supported_formats():
    """
    获取支持的文件格式列表

    Returns:
        文件格式列表
    """
    formats = parser_manager.get_supported_formats()

    return {
        "success": True,
        "formats": formats,
        "count": len(formats)
    }
```

修改 `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import projects, cases, config, vectors, generation, documents

app = FastAPI(
    title="Sisyphus API",
    description="测试用例生成平台 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(cases.router)
app.include_router(config.router)
app.include_router(vectors.router)
app.include_router(generation.router)
app.include_router(documents.router)

@app.get("/")
async def root():
    return {
        "message": "Sisyphus 测试用例生成平台 API",
        "version": "0.1.0",
        "status": "running"
    }
```

**Step 4: Run tests**

```bash
uv run pytest app/tests/test_documents_api.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/documents.py backend/app/main.py
git commit -m "feat: 实现文档解析 API"
```

---

## Task 7: 创建预留的 Skills 目录结构

**Files:**
- Create: `backend/skills/README.md`
- Create: `backend/skills/.gitkeep`

**Step 1: Create skills directory structure**

```bash
mkdir -p backend/skills/{parsers,llm_tools}
```

**Step 2: Create README**

创建 `backend/skills/README.md`:

```markdown
# Skills 目录

此目录用于存放可扩展的插件和工具。

## 目录结构

```
skills/
├── parsers/          # 文档解析插件
│   ├── word.py       # Word 文档解析
│   ├── ppt.py        # PPT 文档解析
│   ├── ocr.py        # 图片 OCR 识别
│   └── web.py        # 网页内容抓取
└── llm_tools/        # LLM 工具插件
    ├── summarizer.py # 文本摘要
    ├── translator.py # 翻译工具
    └── validator.py  # 数据验证
```

## 如何添加新插件

1. 继承 `app.plugins.base.DocumentParser` 基类
2. 实现 `parse()` 和 `supports()` 方法
3. 在 `app/plugins/manager.py` 中注册插件

### 示例

```python
from app.plugins.base import DocumentParser

class WordParser(DocumentParser):
    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() in ['.doc', '.docx']

    def parse(self, file_path: str) -> str:
        # 实现解析逻辑
        pass
```

## 未来扩展

- [ ] Word 文档解析 (python-docx)
- [ ] PPT 文档解析 (python-pptx)
- [ ] 图片 OCR 识别 (PaddleOCR / Tesseract)
- [ ] 网页内容抓取 (BeautifulSoup / Playwright)
- [ ] Excel 表格解析 (openpyxl)
```

**Step 3: Create .gitkeep files**

```bash
touch backend/skills/parsers/.gitkeep
touch backend/skills/llm_tools/.gitkeep
```

**Step 4: Commit**

```bash
git add backend/skills/
git commit -m "feat: 创建预留的 Skills 目录结构"
```

---

## 完成检查清单

- [ ] 文档解析器基类实现完成
- [ ] Markdown、PDF、纯文本解析器实现
- [ ] 插件管理器可以自动选择合适的解析器
- [ ] 文档解析 API 支持文件上传
- [ ] Skills 目录结构创建完成
- [ ] 所有测试通过

## 下一步

继续实施前端部分：
- `2026-03-05-01-frontend-foundation.md` - 前端基础架构
- `2026-03-05-02-frontend-components.md` - 前端组件
- `2026-03-05-03-frontend-websocket.md` - WebSocket 集成
