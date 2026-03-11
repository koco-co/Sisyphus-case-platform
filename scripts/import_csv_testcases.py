"""Import cleaned CSV test cases into the test_cases table and optionally Qdrant.

Usage:
    cd backend
    uv run python ../scripts/import_csv_testcases.py
"""

import asyncio
import csv
import os
import re
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# Load .env from project root
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

# Add backend to path
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.modules.testcases.models import TestCase
from app.modules.products.models import Product, Iteration, Requirement

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/sisyphus",
)

CSV_ROOT = PROJECT_ROOT / "待清洗数据"

PRIORITY_MAP = {
    "高": "P0",
    "中": "P1",
    "低": "P2",
    "最高": "P0",
    "": "P1",
}

CASE_TYPE_MAP = {
    "功能测试": "functional",
    "边界测试": "boundary",
    "异常测试": "exception",
    "性能测试": "performance",
    "安全测试": "security",
    "兼容性测试": "compatibility",
    "": "functional",
}


def parse_steps(steps_text: str, expected_text: str) -> list[dict]:
    """Parse step/expected text into structured step objects."""
    if not steps_text or not steps_text.strip():
        return [{"step": 1, "action": "执行测试", "expected": expected_text.strip() or "验证通过"}]

    step_lines = re.split(r"\n(?=\d+[\.\、])", steps_text.strip())
    expected_lines = re.split(r"\n(?=\d+[\.\、])", expected_text.strip()) if expected_text else []

    result = []
    for i, step_line in enumerate(step_lines):
        action = re.sub(r"^\d+[\.\、]\s*", "", step_line).strip()
        if not action:
            continue
        expected = ""
        if i < len(expected_lines):
            expected = re.sub(r"^\d+[\.\、]\s*", "", expected_lines[i]).strip()
        elif i == 0 and expected_text:
            expected = expected_text.strip()
        result.append({"step": i + 1, "action": action, "expected": expected or "验证通过"})

    return result if result else [{"step": 1, "action": steps_text.strip(), "expected": expected_text.strip() or "验证通过"}]


def extract_tags(keywords: str) -> list[str]:
    """Extract tags from keywords field."""
    if not keywords or not keywords.strip():
        return []
    return [t.strip() for t in re.split(r"[,，;；\s]+", keywords) if t.strip()]


async def ensure_product_and_requirement(
    session: AsyncSession, product_name: str, req_name: str
) -> tuple[uuid.UUID, uuid.UUID]:
    """Get or create product, iteration, and requirement. Returns (product_id, requirement_id)."""
    slug = re.sub(r"[^a-z0-9-]", "-", product_name.lower())[:50] or "imported"

    # Find or create product
    q = select(Product).where(Product.name == product_name, Product.deleted_at.is_(None))
    product = (await session.execute(q)).scalar_one_or_none()
    if not product:
        q2 = select(Product).where(Product.slug == slug, Product.deleted_at.is_(None))
        product = (await session.execute(q2)).scalar_one_or_none()
    if not product:
        product = Product(name=product_name, slug=slug, description=f"从CSV导入的产品: {product_name}")
        session.add(product)
        await session.flush()

    # Find or create a default iteration for imports
    iter_name = f"{product_name}-历史用例"
    q = select(Iteration).where(
        Iteration.product_id == product.id,
        Iteration.name == iter_name,
        Iteration.deleted_at.is_(None),
    )
    iteration = (await session.execute(q)).scalar_one_or_none()
    if not iteration:
        iteration = Iteration(
            product_id=product.id,
            name=iter_name,
            status="completed",
        )
        session.add(iteration)
        await session.flush()

    # Find or create requirement
    req_id_str = f"IMP-{uuid.uuid5(uuid.NAMESPACE_DNS, f'{product_name}/{req_name}').hex[:10].upper()}"
    q = select(Requirement).where(
        Requirement.iteration_id == iteration.id,
        Requirement.title == req_name,
        Requirement.deleted_at.is_(None),
    )
    req = (await session.execute(q)).scalar_one_or_none()
    if not req:
        req = Requirement(
            iteration_id=iteration.id,
            req_id=req_id_str,
            title=req_name,
            content_ast={"type": "doc", "content": [{"type": "paragraph", "text": f"从CSV导入: {req_name}"}]},
            status="approved",
        )
        session.add(req)
        await session.flush()

    return product.id, req.id


def parse_xinyongzhonghe_row(row: dict, case_counter: int) -> dict:
    """Parse a row from 信永中和 format CSV."""
    return {
        "product_name": "信永中和",
        "req_name": row.get("所属模块", "未分类").strip() or "未分类",
        "title": row.get("用例标题", "").strip(),
        "precondition": row.get("前置条件", "").strip() or None,
        "steps_text": row.get("步骤", ""),
        "expected_text": row.get("预期", ""),
        "keywords": row.get("关键词", ""),
        "priority": row.get("优先级", ""),
        "case_type": row.get("用例类型", ""),
        "module_path": row.get("所属模块", "").strip(),
    }


def parse_shuzhan_row(row: dict, case_counter: int) -> dict:
    """Parse a row from 数栈平台 format CSV."""
    product_raw = row.get("所属产品", "数栈平台").strip()
    product_name = re.sub(r"\(#\d+\)", "", product_raw).strip() or "数栈平台"
    module_raw = row.get("所属模块", "").strip()
    # Extract the requirement name from module path like "/版本迭代测试用例/v6.4.8/【规则调度设置】任务时长限制(#10220)"
    parts = module_raw.strip("/").split("/")
    req_name = parts[-1] if parts else "未分类"
    req_name = re.sub(r"\(#\d+\)", "", req_name).strip() or "未分类"

    return {
        "product_name": product_name,
        "req_name": req_name,
        "title": row.get("用例标题", "").strip(),
        "precondition": row.get("前置条件", "").strip() or None,
        "steps_text": row.get("步骤", ""),
        "expected_text": row.get("预期", ""),
        "keywords": row.get("关键词", ""),
        "priority": row.get("优先级", ""),
        "case_type": row.get("用例类型", ""),
        "module_path": module_raw,
    }


def detect_format(header: list[str]) -> str:
    """Detect CSV format based on header columns."""
    if "用例编号" in header:
        return "shuzhan"
    return "xinyongzhonghe"


async def import_csv_file(session: AsyncSession, filepath: Path, stats: dict) -> None:
    """Import a single CSV file."""
    print(f"  📄 {filepath.name}")

    try:
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"    ⚠️ 空文件，跳过")
                return

            fmt = detect_format(list(reader.fieldnames))
            parse_fn = parse_shuzhan_row if fmt == "shuzhan" else parse_xinyongzhonghe_row

            req_cache: dict[tuple[str, str], tuple[uuid.UUID, uuid.UUID]] = {}
            count = 0

            for i, row in enumerate(reader):
                try:
                    parsed = parse_fn(row, i)
                    if not parsed["title"]:
                        continue

                    cache_key = (parsed["product_name"], parsed["req_name"])
                    if cache_key not in req_cache:
                        req_cache[cache_key] = await ensure_product_and_requirement(
                            session, parsed["product_name"], parsed["req_name"]
                        )
                    _, req_id = req_cache[cache_key]

                    case_id = f"IMP-{uuid.uuid4().hex[:8].upper()}"

                    # Check idempotency by title + requirement
                    q = select(TestCase).where(
                        TestCase.requirement_id == req_id,
                        TestCase.title == parsed["title"],
                        TestCase.deleted_at.is_(None),
                    )
                    existing = (await session.execute(q)).scalar_one_or_none()
                    if existing:
                        stats["skipped"] += 1
                        continue

                    steps = parse_steps(parsed["steps_text"], parsed["expected_text"])
                    tags = extract_tags(parsed["keywords"])
                    priority_raw = parsed["priority"].strip()
                    priority = PRIORITY_MAP.get(priority_raw, "P1")
                    case_type_raw = parsed["case_type"].strip()
                    case_type = CASE_TYPE_MAP.get(case_type_raw, "functional")

                    tc = TestCase(
                        requirement_id=req_id,
                        case_id=case_id,
                        title=parsed["title"],
                        module_path=parsed["module_path"] or None,
                        precondition=parsed["precondition"],
                        priority=priority,
                        case_type=case_type,
                        status="approved",
                        source="imported",
                        steps=[{"step": s["step"], "action": s["action"], "expected": s["expected"]} for s in steps],
                        tags=tags,
                        clean_status="cleaned",
                        original_raw=dict(row),
                    )
                    session.add(tc)
                    count += 1
                    stats["imported"] += 1

                    if count % 50 == 0:
                        await session.flush()

                except Exception as e:
                    stats["errors"] += 1
                    if stats["errors"] <= 5:
                        print(f"    ❌ Row {i}: {e}")

            await session.flush()
            print(f"    ✅ {count} 条用例导入")

    except Exception as e:
        print(f"    ❌ 文件读取失败: {e}")
        stats["errors"] += 1


async def main():
    print("🚀 开始导入 CSV 测试用例到数据库...\n")

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    stats = {"imported": 0, "skipped": 0, "errors": 0, "files": 0}

    csv_files = sorted(CSV_ROOT.rglob("*.csv"))
    print(f"📂 发现 {len(csv_files)} 个 CSV 文件\n")

    async with async_session() as session:
        async with session.begin():
            for filepath in csv_files:
                stats["files"] += 1
                await import_csv_file(session, filepath, stats)

    await engine.dispose()

    print(f"\n{'='*50}")
    print(f"📊 导入结果:")
    print(f"  文件数: {stats['files']}")
    print(f"  导入: {stats['imported']} 条用例")
    print(f"  跳过(重复): {stats['skipped']} 条")
    print(f"  错误: {stats['errors']} 条")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
