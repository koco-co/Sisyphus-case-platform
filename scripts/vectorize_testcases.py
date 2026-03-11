"""将 PostgreSQL 中的历史测试用例向量化并存入 Qdrant。

用例文本 = 标题 + 前置条件 + 步骤（action + expected_result）
嵌入模型：根据 .env LLM_PROVIDER 自动选择（zhipu → embedding-3）

Usage:
    cd backend
    uv run python ../scripts/vectorize_testcases.py [--batch-size 32] [--collection historical_testcases]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time

# ── 路径 & 环境变量 ─────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

env_path = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k] = v

os.chdir(BACKEND_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vectorize")

# ── 延迟导入（需要 env 先就位）─────────────────────────────────
from qdrant_client import QdrantClient, models  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import get_engine  # noqa: E402
from app.engine.rag.embedder import EMBEDDING_DIMENSION, embed_texts  # noqa: E402

COLLECTION = "historical_testcases"
PROGRESS_FILE = os.path.join(PROJECT_ROOT, "scripts", ".vectorize_progress.json")


# ═══════════════════════════════════════════════════════════════════
# 1. 从 PostgreSQL 读取用例
# ═══════════════════════════════════════════════════════════════════

async def load_testcases(engine) -> list[dict]:
    """读取所有未删除的用例，含关联的产品和需求名称。"""
    sql = text("""
        SELECT
            tc.id,
            tc.title,
            tc.precondition,
            tc.steps,
            tc.priority,
            tc.case_type,
            tc.module_path,
            r.title AS req_title,
            p.name  AS product_name
        FROM test_cases tc
        LEFT JOIN requirements r ON tc.requirement_id = r.id
        LEFT JOIN iterations it ON r.iteration_id = it.id
        LEFT JOIN products p ON it.product_id = p.id
        WHERE tc.deleted_at IS NULL
        ORDER BY tc.id
    """)
    async with engine.connect() as conn:
        rows = await conn.execute(sql)
        return [dict(row._mapping) for row in rows]


# ═══════════════════════════════════════════════════════════════════
# 2. 用例 → 嵌入文本
# ═══════════════════════════════════════════════════════════════════

def _sanitize(text: str, max_len: int = 2000) -> str:
    """清理文本：移除特殊 Unicode、控制字符，截断到 max_len。"""
    import re as _re
    # 移除控制字符（保留换行和空格）
    text = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # 替换可能导致 API 错误的特殊 Unicode 字符
    text = text.replace("\u200b", "").replace("\ufeff", "")
    return text[:max_len].strip()


def testcase_to_text(tc: dict) -> str:
    """将一条用例转换为适合嵌入的文本描述。"""
    parts: list[str] = []

    if tc.get("product_name"):
        parts.append(f"产品: {tc['product_name']}")
    if tc.get("module_path"):
        parts.append(f"模块: {tc['module_path']}")
    if tc.get("req_title"):
        parts.append(f"需求: {tc['req_title']}")

    parts.append(f"用例: {tc['title'] or '(无标题)'}")

    if tc.get("priority"):
        parts.append(f"优先级: {tc['priority']}")

    if tc.get("precondition"):
        parts.append(f"前置条件: {tc['precondition']}")

    steps = tc.get("steps")
    if steps:
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except (json.JSONDecodeError, TypeError):
                parts.append(f"步骤: {steps}")
                steps = None

        if isinstance(steps, list):
            step_lines: list[str] = []
            for i, s in enumerate(steps, 1):
                if isinstance(s, dict):
                    action = s.get("action", s.get("description", ""))
                    expected = s.get("expected_result", s.get("expected", ""))
                    step_lines.append(f"  {i}. {action}")
                    if expected:
                        step_lines.append(f"     预期: {expected}")
                else:
                    step_lines.append(f"  {i}. {s}")
            if step_lines:
                parts.append("步骤:\n" + "\n".join(step_lines))

    return _sanitize("\n".join(parts))


# ═══════════════════════════════════════════════════════════════════
# 3. Qdrant 入库
# ═══════════════════════════════════════════════════════════════════

def ensure_collection(client: QdrantClient, collection: str) -> None:
    names = [c.name for c in client.get_collections().collections]
    if collection not in names:
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )
        logger.info("创建 Qdrant collection: %s (dim=%d)", collection, EMBEDDING_DIMENSION)
    else:
        logger.info("collection '%s' 已存在", collection)


def load_progress() -> set[str]:
    """加载已完成的用例 ID 集合（断点续传）。"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return set(json.load(f))
    return set()


def save_progress(done_ids: set[str]) -> None:
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(done_ids), f)


# ═══════════════════════════════════════════════════════════════════
# 4. 主流程
# ═══════════════════════════════════════════════════════════════════

async def main(batch_size: int = 16, collection: str = COLLECTION) -> None:
    engine = get_engine()

    logger.info("加载用例数据...")
    testcases = await load_testcases(engine)
    logger.info("共 %d 条用例", len(testcases))

    # Qdrant
    client = QdrantClient(url=settings.qdrant_url, timeout=30, trust_env=False)
    ensure_collection(client, collection)

    # 断点续传
    done_ids = load_progress()
    remaining = [tc for tc in testcases if str(tc["id"]) not in done_ids]
    logger.info("已完成 %d, 待处理 %d", len(done_ids), len(remaining))

    if not remaining:
        logger.info("全部已完成！")
        await engine.dispose()
        return

    total = len(remaining)
    success = 0
    errors = 0
    start_time = time.time()

    for i in range(0, total, batch_size):
        batch = remaining[i : i + batch_size]
        texts = [testcase_to_text(tc) for tc in batch]

        try:
            vectors = await embed_texts(texts, batch_size=batch_size)
        except Exception as e:
            logger.warning("批量嵌入失败 (batch %d-%d): %s，降级为逐条处理", i, i + len(batch), e)
            # 遇到 rate limit 等待
            if "429" in str(e) or "rate" in str(e).lower():
                await asyncio.sleep(10)
            # 降级：逐条嵌入，跳过失败的单条
            vectors = []
            failed_indices: set[int] = set()
            for j, t in enumerate(texts):
                try:
                    v = await embed_texts([t], batch_size=1)
                    vectors.append(v[0])
                except Exception:
                    logger.warning("  跳过用例: %s", batch[j].get("title", "?")[:50])
                    vectors.append(None)  # type: ignore[arg-type]
                    failed_indices.add(j)
                    errors += 1

            # 过滤掉失败的
            batch = [tc for j, tc in enumerate(batch) if j not in failed_indices]
            texts = [t for j, t in enumerate(texts) if j not in failed_indices]
            vectors = [v for v in vectors if v is not None]

            if not vectors:
                continue

        points: list[models.PointStruct] = []
        for tc, vec in zip(batch, vectors, strict=True):
            payload = {
                "testcase_id": str(tc["id"]),
                "title": tc["title"],
                "product": tc.get("product_name", ""),
                "module": tc.get("module_path", ""),
                "requirement": tc.get("req_title", ""),
                "priority": tc.get("priority", ""),
                "case_type": tc.get("case_type", ""),
                "content": testcase_to_text(tc),
            }
            points.append(
                models.PointStruct(
                    id=str(tc["id"]),
                    vector=vec,
                    payload=payload,
                )
            )

        try:
            client.upsert(collection_name=collection, points=points)
            batch_ids = {str(tc["id"]) for tc in batch}
            done_ids.update(batch_ids)
            success += len(batch)
        except Exception as e:
            logger.error("Qdrant 写入失败: %s", e)
            errors += len(batch)
            continue

        # 进度
        elapsed = time.time() - start_time
        rate = success / elapsed if elapsed > 0 else 0
        eta = (total - i - len(batch)) / rate if rate > 0 else 0
        logger.info(
            "进度: %d/%d (%.1f%%) | 成功 %d | 错误 %d | %.1f条/s | ETA %.0fs",
            i + len(batch), total, (i + len(batch)) / total * 100,
            success, errors, rate, eta,
        )

        # 每 5 批保存进度
        if (i // batch_size) % 5 == 4:
            save_progress(done_ids)

        # 避免 rate limit
        await asyncio.sleep(0.5)

    save_progress(done_ids)
    await engine.dispose()

    elapsed = time.time() - start_time
    logger.info(
        "向量化完成: 成功 %d, 错误 %d, 耗时 %.1fs",
        success, errors, elapsed,
    )

    # 验证
    info = client.get_collection(collection)
    logger.info("Qdrant collection '%s': %d points", collection, info.points_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="向量化历史测试用例到 Qdrant")
    parser.add_argument("--batch-size", type=int, default=16, help="嵌入批大小")
    parser.add_argument("--collection", default=COLLECTION, help="Qdrant collection 名称")
    args = parser.parse_args()

    asyncio.run(main(batch_size=args.batch_size, collection=args.collection))
