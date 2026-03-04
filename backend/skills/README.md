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
3. 在 `app.plugins/manager.py` 中注册插件

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
