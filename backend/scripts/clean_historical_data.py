"""历史测试用例数据清洗脚本。

功能：
1. 读取 待清洗数据/ 下的 CSV 文件
2. HTML 实体解码
3. 优先级标准化（统一为 P0-P3）
4. 字段统一映射
5. 去重
6. 输出清洗后的 JSON（供后续向量化入库）

用法：
    cd backend
    uv run python scripts/clean_historical_data.py
"""

from __future__ import annotations

import csv
import html
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from hashlib import md5
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "待清洗数据"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "data" / "cleaned"

# ═══════════════════════════════════════════════════════════════════
# 统一数据模型
# ═══════════════════════════════════════════════════════════════════


@dataclass
class CleanedTestCase:
    """清洗后的统一测试用例格式。"""

    source: str  # 数据来源（信永中和 / 数栈平台）
    module: str  # 所属模块
    title: str  # 用例标题
    preconditions: str  # 前置条件
    steps: list[str]  # 操作步骤（列表）
    expected: list[str]  # 预期结果（列表）
    keywords: list[str]  # 关键词
    priority: str  # P0/P1/P2/P3
    case_type: str  # 用例类型
    stage: str  # 适用阶段
    requirement: str = ""  # 关联需求
    product: str = ""  # 所属产品
    tags: list[str] = field(default_factory=list)

    @property
    def content_hash(self) -> str:
        """用于去重的内容指纹。"""
        key = f"{self.module}|{self.title}|{'|'.join(self.steps)}"
        return md5(key.encode()).hexdigest()

    def to_chunk_text(self) -> str:
        """转换为适合向量化的文本块。"""
        parts = [
            f"【模块】{self.module}",
            f"【标题】{self.title}",
        ]
        if self.preconditions:
            parts.append(f"【前置条件】{self.preconditions}")
        if self.steps:
            steps_text = "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(self.steps))
            parts.append(f"【操作步骤】\n{steps_text}")
        if self.expected:
            expected_text = "\n".join(f"  {i + 1}. {e}" for i, e in enumerate(self.expected))
            parts.append(f"【预期结果】\n{expected_text}")
        if self.keywords:
            parts.append(f"【关键词】{', '.join(self.keywords)}")
        parts.append(f"【优先级】{self.priority}")
        if self.requirement:
            parts.append(f"【关联需求】{self.requirement}")
        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
# 清洗工具函数
# ═══════════════════════════════════════════════════════════════════


def clean_html(text: str) -> str:
    """移除 HTML 标签并解码实体。"""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p>|</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_priority(raw: str, source: str = "") -> str:
    """统一优先级为 P0(最高) ~ P3(最低)。

    信永中和/数栈平台均使用 1-3 尺度：
    - 1 → P0（高）
    - 2 → P1（中）
    - 3 → P2（低）
    """
    raw = raw.strip()
    mapping = {"1": "P0", "2": "P1", "3": "P2"}
    return mapping.get(raw, "P1")


def split_steps(text: str) -> list[str]:
    """将步骤/预期文本拆分为列表。"""
    if not text:
        return []
    text = clean_html(text)
    # 按 "1. " "2. " 等编号拆分
    parts = re.split(r"\n?\d+[\.\)、]\s*", text)
    # 或按换行拆分
    if len(parts) <= 1:
        parts = [line.strip() for line in text.split("\n") if line.strip()]
    else:
        parts = [p.strip() for p in parts if p.strip()]
    return parts


def extract_keywords(text: str) -> list[str]:
    """从关键词字段提取列表。"""
    if not text:
        return []
    text = clean_html(text)
    delimiters = re.compile(r"[,，;；\s]+")
    return [kw.strip() for kw in delimiters.split(text) if kw.strip()]


def clean_precondition(text: str) -> str:
    """清洗前置条件，移除 SQL 脚本但保留业务描述。"""
    if not text:
        return ""
    text = clean_html(text)
    lines = text.split("\n")
    clean_lines = []
    in_sql = False
    for line in lines:
        stripped = line.strip().upper()
        if any(
            stripped.startswith(kw) for kw in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ", "ALTER ", "DROP ")
        ):
            in_sql = True
            continue
        if in_sql and stripped.endswith(";"):
            in_sql = False
            continue
        if not in_sql:
            clean_lines.append(line)
    return "\n".join(clean_lines).strip()


# ═══════════════════════════════════════════════════════════════════
# 数据源解析器
# ═══════════════════════════════════════════════════════════════════


def parse_xinyonghe(csv_path: Path) -> list[CleanedTestCase]:
    """解析信永中和 CSV。"""
    cases: list[CleanedTestCase] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case = CleanedTestCase(
                source="信永中和",
                module=clean_html(row.get("所属模块", "")),
                title=clean_html(row.get("用例标题", "")),
                preconditions=clean_precondition(row.get("前置条件", "")),
                steps=split_steps(row.get("步骤", "")),
                expected=split_steps(row.get("预期", "")),
                keywords=extract_keywords(row.get("关键词", "")),
                priority=normalize_priority(row.get("优先级", "2")),
                case_type=row.get("用例类型", "功能测试").strip(),
                stage=row.get("适用阶段", "功能测试阶段").strip(),
            )
            if case.title:
                cases.append(case)
    logger.info("信永中和: 解析 %d 条用例", len(cases))
    return cases


def parse_shuzhan(data_dir: Path) -> list[CleanedTestCase]:
    """解析数栈平台目录下所有 CSV。"""
    cases: list[CleanedTestCase] = []
    for csv_path in sorted(data_dir.rglob("*.csv")):
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    case = CleanedTestCase(
                        source="数栈平台",
                        product=clean_html(row.get("所属产品", "")),
                        module=clean_html(row.get("所属模块", "")),
                        requirement=clean_html(row.get("相关需求", "")),
                        title=clean_html(row.get("用例标题", "")),
                        preconditions=clean_precondition(row.get("前置条件", "")),
                        steps=split_steps(row.get("步骤", "")),
                        expected=split_steps(row.get("预期", "")),
                        keywords=extract_keywords(row.get("关键词", "")),
                        priority=normalize_priority(row.get("优先级", "2")),
                        case_type=row.get("用例类型", "功能测试").strip(),
                        stage=row.get("适用阶段", "功能测试阶段").strip(),
                    )
                    if case.title:
                        cases.append(case)
        except Exception as e:
            logger.warning("解析失败 %s: %s", csv_path, e)
    logger.info("数栈平台: 解析 %d 条用例", len(cases))
    return cases


# ═══════════════════════════════════════════════════════════════════
# 去重
# ═══════════════════════════════════════════════════════════════════


def deduplicate(cases: list[CleanedTestCase]) -> list[CleanedTestCase]:
    """基于内容指纹去重。"""
    seen: set[str] = set()
    unique: list[CleanedTestCase] = []
    for case in cases:
        h = case.content_hash
        if h not in seen:
            seen.add(h)
            unique.append(case)
    removed = len(cases) - len(unique)
    if removed > 0:
        logger.info("去重: 移除 %d 条重复用例", removed)
    return unique


# ═══════════════════════════════════════════════════════════════════
# 质量过滤
# ═══════════════════════════════════════════════════════════════════


def quality_filter(cases: list[CleanedTestCase]) -> list[CleanedTestCase]:
    """过滤低质量用例。"""
    filtered: list[CleanedTestCase] = []
    removed = 0
    for case in cases:
        # 标题太短
        if len(case.title) < 4:
            removed += 1
            continue
        # 没有步骤也没有预期
        if not case.steps and not case.expected:
            removed += 1
            continue
        filtered.append(case)
    if removed > 0:
        logger.info("质量过滤: 移除 %d 条低质量用例", removed)
    return filtered


# ═══════════════════════════════════════════════════════════════════
# 规范提取（用于更新 Prompt/Rules）
# ═══════════════════════════════════════════════════════════════════


def extract_conventions(cases: list[CleanedTestCase]) -> dict:
    """从清洗后的用例中提取编写规范。"""
    step_patterns: dict[str, int] = {}
    avg_steps = 0
    avg_expected = 0
    modules: set[str] = set()
    priorities: dict[str, int] = {}

    for case in cases:
        avg_steps += len(case.steps)
        avg_expected += len(case.expected)
        modules.add(case.module)
        priorities[case.priority] = priorities.get(case.priority, 0) + 1

        for step in case.steps:
            # 提取动词模式
            verb_pattern = r"^(点击|输入|选择|进入|验证|检查|打开|切换|勾选|填写|提交|删除|编辑|查看|搜索|新增)"
            verbs = re.findall(verb_pattern, step)
            for v in verbs:
                step_patterns[v] = step_patterns.get(v, 0) + 1

    total = len(cases)
    conventions = {
        "total_cases": total,
        "avg_steps_per_case": round(avg_steps / total, 1) if total else 0,
        "avg_expected_per_case": round(avg_expected / total, 1) if total else 0,
        "priority_distribution": priorities,
        "unique_modules": len(modules),
        "common_step_verbs": dict(sorted(step_patterns.items(), key=lambda x: -x[1])[:15]),
        "step_writing_pattern": "动词 + 对象 + 操作描述（如：点击【保存】按钮）",
        "expected_writing_pattern": "主语 + 状态/行为描述（如：页面成功跳转到列表页）",
    }
    return conventions


# ═══════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════


def main() -> None:
    """执行完整清洗流程。"""
    logger.info("=" * 60)
    logger.info("开始历史测试用例数据清洗")
    logger.info("=" * 60)

    all_cases: list[CleanedTestCase] = []

    # 1. 解析信永中和
    xyh_csv = DATA_DIR / "信永中和" / "信永中和测试用例(1~12).csv"
    if xyh_csv.exists():
        all_cases.extend(parse_xinyonghe(xyh_csv))

    # 2. 解析数栈平台
    sz_dir = DATA_DIR / "数栈平台"
    if sz_dir.exists():
        all_cases.extend(parse_shuzhan(sz_dir))

    logger.info("总计解析: %d 条用例", len(all_cases))

    # 3. 去重
    all_cases = deduplicate(all_cases)

    # 4. 质量过滤
    all_cases = quality_filter(all_cases)

    logger.info("清洗后: %d 条有效用例", len(all_cases))

    # 5. 提取规范
    conventions = extract_conventions(all_cases)
    logger.info("规范提取完成: %s", json.dumps(conventions, ensure_ascii=False, indent=2))

    # 6. 输出
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 输出清洗后的用例
    cases_output = OUTPUT_DIR / "cleaned_testcases.json"
    with open(cases_output, "w", encoding="utf-8") as f:
        json.dump(
            [asdict(c) for c in all_cases],
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("用例数据已输出: %s (%d 条)", cases_output, len(all_cases))

    # 输出用于向量化的文本块
    chunks_output = OUTPUT_DIR / "vectorize_chunks.jsonl"
    with open(chunks_output, "w", encoding="utf-8") as f:
        for case in all_cases:
            chunk = {
                "text": case.to_chunk_text(),
                "metadata": {
                    "source": case.source,
                    "module": case.module,
                    "title": case.title,
                    "priority": case.priority,
                    "product": case.product,
                    "requirement": case.requirement,
                    "case_type": case.case_type,
                },
            }
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    logger.info("向量化文本块已输出: %s", chunks_output)

    # 输出规范文件
    conventions_output = OUTPUT_DIR / "conventions.json"
    with open(conventions_output, "w", encoding="utf-8") as f:
        json.dump(conventions, f, ensure_ascii=False, indent=2)
    logger.info("规范提取已输出: %s", conventions_output)

    logger.info("=" * 60)
    logger.info("清洗完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
