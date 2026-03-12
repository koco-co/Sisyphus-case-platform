"""SSE 收集器 — 流式输出的同时收集完整响应文本，用于持久化。

额外功能：增量解析 JSON 数组，每完成一个 case 对象立刻发出 `case` SSE 事件，
前端无需等待完整 JSON 即可实时渲染用例卡片。
"""

import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable

logger = logging.getLogger(__name__)


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class _IncrementalCaseExtractor:
    """从流式 content delta 中增量提取完整 JSON case 对象。

    支持两种格式：
    - 纯 JSON 数组：``[{"title":...}, ...]``
    - Markdown 代码块：````json\\n[...]\\n```​``

    算法：字符级状态机，追踪括号深度和字符串边界，
    一旦深度从 2 降回 1（即顶层 `{...}` 闭合），立即提取并解析。
    """

    def __init__(self) -> None:
        self._buf = ""
        self._scan_pos = 0
        self._in_array = False
        self._depth = 0  # 1 = 在数组顶层，2+ = 在对象/嵌套结构内
        self._in_string = False
        self._escape_next = False
        self._obj_start = -1
        self._case_index = 0

    def feed(self, delta: str) -> list[dict]:
        """喂入一个 content delta，返回本次新完成的 case 字典列表。"""
        self._buf += delta
        result: list[dict] = []

        while self._scan_pos < len(self._buf):
            ch = self._buf[self._scan_pos]

            if self._escape_next:
                self._escape_next = False
                self._scan_pos += 1
                continue

            if self._in_string:
                if ch == "\\":
                    self._escape_next = True
                elif ch == '"':
                    self._in_string = False
                self._scan_pos += 1
                continue

            # 非字符串区域
            if ch == '"':
                self._in_string = True
            elif not self._in_array and ch == "[":
                # 找到数组起始（忽略字符串内的 [）
                self._in_array = True
                self._depth = 1
            elif self._in_array:
                if ch in ("{", "["):
                    if ch == "{" and self._depth == 1:
                        self._obj_start = self._scan_pos
                    self._depth += 1
                elif ch in ("}", "]"):
                    self._depth -= 1
                    if ch == "}" and self._depth == 1 and self._obj_start != -1:
                        obj_str = self._buf[self._obj_start : self._scan_pos + 1]
                        try:
                            case = json.loads(obj_str)
                            if isinstance(case, dict) and case.get("title"):
                                case["_idx"] = self._case_index
                                self._case_index += 1
                                result.append(case)
                        except json.JSONDecodeError:
                            pass
                        self._obj_start = -1
                    elif self._depth == 0:
                        self._in_array = False

            self._scan_pos += 1

        return result


class SSECollector:
    """Wraps an SSE async generator, collecting content while streaming.

    同时进行增量 case 解析：每完成一个 JSON case 对象立刻在流中插入
    ``event: case`` 事件，前端可实时渲染用例卡片。

    Usage::

        collector = SSECollector(stream, on_complete=save_to_db)
        return StreamingResponse(collector, media_type="text/event-stream")
    """

    def __init__(
        self,
        stream: AsyncIterator[str],
        on_complete: Callable[[str], Awaitable[None]],
    ) -> None:
        self._stream = stream
        self._on_complete = on_complete
        self._chunks: list[str] = []
        self._extractor = _IncrementalCaseExtractor()

    async def __aiter__(self):  # noqa: ANN204
        try:
            async for chunk in self._stream:
                yield chunk
                delta = self._parse_chunk(chunk)
                if delta:
                    for case in self._extractor.feed(delta):
                        yield _sse_event("case", case)

            full_text = "".join(self._chunks)
            try:
                await self._on_complete(full_text)
            except Exception:
                logger.exception("SSECollector on_complete callback failed")
        except Exception as exc:
            logger.exception("SSECollector stream error")
            error_msg = str(exc) or "AI 服务异常，请稍后重试"
            yield _sse_event("error", {"message": error_msg})
            yield _sse_event("done", {"usage": {}})

    # ------------------------------------------------------------------

    def _parse_chunk(self, raw: str) -> str:
        """Extract content delta from an SSE chunk, also accumulate full text.

        Expected format::

            event: content
            data: {"delta": "some text"}

        Returns the delta string (empty if not a content event).
        """
        event_type = ""
        for line in raw.strip().split("\n"):
            if line.startswith("event: "):
                event_type = line[7:].strip()
            elif line.startswith("data: ") and event_type == "content":
                try:
                    data = json.loads(line[6:])
                    if "delta" in data:
                        delta: str = data["delta"]
                        self._chunks.append(delta)
                        return delta
                except (json.JSONDecodeError, KeyError):
                    pass
        return ""
