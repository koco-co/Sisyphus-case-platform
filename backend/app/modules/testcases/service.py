import uuid as _uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.testcases.models import TestCase, TestCaseVersion
from app.modules.testcases.schemas import TestCaseCreate, TestCaseUpdate


class TestCaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── List (paginated + filtered) ────────────────────────────────

    async def list_cases(
        self,
        *,
        requirement_id: UUID | None = None,
        scene_node_id: UUID | None = None,
        status_filter: str | None = None,
        clean_status: str | None = None,
        priority: str | None = None,
        case_type: str | None = None,
        source: str | None = None,
        keyword: str | None = None,
        module_path: str | None = None,
        folder_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestCase], int]:
        q = select(TestCase).where(TestCase.deleted_at.is_(None))
        count_q = select(func.count(TestCase.id)).select_from(TestCase).where(TestCase.deleted_at.is_(None))

        for col, val in (
            (TestCase.requirement_id, requirement_id),
            (TestCase.scene_node_id, scene_node_id),
            (TestCase.priority, priority),
        ):
            if val is not None:
                q = q.where(col == val)
                count_q = count_q.where(col == val)

        if status_filter is not None:
            statuses = [status_filter]
            if status_filter == "approved":
                statuses.append("active")
            elif status_filter == "review":
                statuses.append("pending_review")
            if len(statuses) == 1:
                q = q.where(TestCase.status == status_filter)
                count_q = count_q.where(TestCase.status == status_filter)
            else:
                q = q.where(TestCase.status.in_(statuses))
                count_q = count_q.where(TestCase.status.in_(statuses))

        if clean_status is not None:
            q = q.where(TestCase.clean_status == clean_status)
            count_q = count_q.where(TestCase.clean_status == clean_status)

        if case_type is not None:
            case_types = [case_type]
            if case_type == "functional":
                case_types.append("normal")
            if len(case_types) == 1:
                q = q.where(TestCase.case_type == case_type)
                count_q = count_q.where(TestCase.case_type == case_type)
            else:
                q = q.where(TestCase.case_type.in_(case_types))
                count_q = count_q.where(TestCase.case_type.in_(case_types))

        if source is not None:
            sources = [source]
            if source == "ai_generated":
                sources.append("ai")
            if len(sources) == 1:
                q = q.where(TestCase.source == source)
                count_q = count_q.where(TestCase.source == source)
            else:
                q = q.where(TestCase.source.in_(sources))
                count_q = count_q.where(TestCase.source.in_(sources))

        if keyword:
            keyword_filter = or_(
                TestCase.title.ilike(f"%{keyword}%"),
                TestCase.case_id.ilike(f"%{keyword}%"),
            )
            q = q.where(keyword_filter)
            count_q = count_q.where(keyword_filter)

        if module_path is not None:
            if module_path == "__uncategorized__":
                # 查询未分类（module_path 为 NULL 或空字符串）的用例
                uncategorized_filter = or_(TestCase.module_path.is_(None), TestCase.module_path == "")
                q = q.where(uncategorized_filter)
                count_q = count_q.where(uncategorized_filter)
            else:
                # 精确匹配或前缀匹配（以该目录开头的所有子路径）
                path_filter = or_(
                    TestCase.module_path == module_path,
                    TestCase.module_path.like(f"{module_path}/%"),
                )
                q = q.where(path_filter)
                count_q = count_q.where(path_filter)

        if folder_id is not None:
            q = q.where(TestCase.folder_id == folder_id)
            count_q = count_q.where(TestCase.folder_id == folder_id)

        total = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(TestCase.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    # ── Single read ────────────────────────────────────────────────

    async def get_case(self, case_id: UUID) -> TestCase:
        q = select(TestCase).where(TestCase.id == case_id, TestCase.deleted_at.is_(None))
        result = await self.session.execute(q)
        tc = result.scalar_one_or_none()
        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test case not found",
            )
        return tc

    # ── Idempotent create ──────────────────────────────────────────

    async def create_case(self, data: TestCaseCreate) -> TestCase:
        case_id_str = data.case_id or f"TC-{_uuid.uuid4().hex[:8].upper()}"

        # Idempotent: if caller-supplied case_id exists, return it
        if data.case_id:
            q = select(TestCase).where(
                TestCase.case_id == case_id_str,
                TestCase.deleted_at.is_(None),
            )
            existing = (await self.session.execute(q)).scalar_one_or_none()
            if existing:
                return existing

        payload = data.model_dump(exclude={"case_id"})
        tc = TestCase(**payload, case_id=case_id_str)
        self.session.add(tc)
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    # ── Update (with version snapshot) ─────────────────────────────

    async def update_case(self, case_id: UUID, data: TestCaseUpdate) -> TestCase:
        tc = await self.get_case(case_id)

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return tc

        await self._create_version(tc)
        for key, value in updates.items():
            setattr(tc, key, value)
        tc.version += 1

        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    # ── Soft delete ────────────────────────────────────────────────

    async def soft_delete_case(self, case_id: UUID) -> None:
        tc = await self.get_case(case_id)
        tc.deleted_at = datetime.now(UTC)
        await self.session.commit()

    # ── Batch status update ────────────────────────────────────────

    async def batch_update_status(self, case_ids: list[UUID], new_status: str) -> int:
        count = 0
        for cid in case_ids:
            q = select(TestCase).where(TestCase.id == cid, TestCase.deleted_at.is_(None))
            tc = (await self.session.execute(q)).scalar_one_or_none()
            if tc:
                tc.status = new_status
                count += 1
        await self.session.commit()
        return count

    # ── Convenience queries ────────────────────────────────────────

    async def get_cases_by_requirement(self, requirement_id: UUID) -> list[TestCase]:
        q = (
            select(TestCase)
            .where(
                TestCase.requirement_id == requirement_id,
                TestCase.deleted_at.is_(None),
            )
            .order_by(TestCase.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_cases_by_scene_node(self, node_id: UUID) -> list[TestCase]:
        q = (
            select(TestCase)
            .where(
                TestCase.scene_node_id == node_id,
                TestCase.deleted_at.is_(None),
            )
            .order_by(TestCase.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def count_by_status(self, requirement_id: UUID | None = None) -> tuple[int, list[dict[str, object]]]:
        q = (
            select(TestCase.status, func.count(TestCase.id))
            .where(TestCase.deleted_at.is_(None))
            .group_by(TestCase.status)
        )
        if requirement_id:
            q = q.where(TestCase.requirement_id == requirement_id)

        result = await self.session.execute(q)
        rows = result.all()
        total = sum(row[1] for row in rows)
        by_status = [{"status": row[0], "count": row[1]} for row in rows]
        return total, by_status

    # ── Version management (B-M06-05) ─────────────────────────────

    async def list_versions(self, case_id: UUID) -> list[TestCaseVersion]:
        q = (
            select(TestCaseVersion)
            .where(TestCaseVersion.test_case_id == case_id)
            .order_by(TestCaseVersion.version.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_version(self, case_id: UUID, version: int) -> TestCaseVersion:
        q = select(TestCaseVersion).where(
            TestCaseVersion.test_case_id == case_id,
            TestCaseVersion.version == version,
        )
        result = await self.session.execute(q)
        ver = result.scalar_one_or_none()
        if not ver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found",
            )
        return ver

    # ── Review workflow (B-M06-06) ─────────────────────────────────

    async def submit_for_review(self, case_id: UUID) -> TestCase:
        tc = await self.get_case(case_id)
        if tc.status not in ("draft", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit for review from status '{tc.status}'",
            )
        await self._create_version(tc, change_reason="Submitted for review")
        tc.status = "review"
        tc.version += 1
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def approve_case(self, case_id: UUID, reviewer_id: UUID) -> TestCase:
        tc = await self.get_case(case_id)
        if tc.status != "review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only cases in 'review' status can be approved",
            )
        await self._create_version(tc, change_reason=f"Approved by {reviewer_id}")
        tc.status = "approved"
        tc.reviewer_id = reviewer_id
        tc.review_comment = None
        tc.version += 1
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def reject_case(self, case_id: UUID, reviewer_id: UUID, reason: str | None = None) -> TestCase:
        tc = await self.get_case(case_id)
        if tc.status != "review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only cases in 'review' status can be rejected",
            )
        await self._create_version(tc, change_reason=f"Rejected: {reason or 'No reason given'}")
        tc.status = "rejected"
        tc.reviewer_id = reviewer_id
        tc.review_comment = reason
        tc.version += 1
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    # ── Full traceability (B-M06-07) ──────────────────────────────

    async def get_traceability(self, case_id: UUID) -> dict:
        """Return full traceability chain: TestCase → TestPoint → SceneMap → Requirement → Iteration → Product."""
        from app.modules.products.models import Iteration, Product, Requirement
        from app.modules.scene_map.models import SceneMap, TestPoint

        tc = await self.get_case(case_id)

        result: dict[str, object] = {"test_case": tc}

        # TestPoint (via scene_node_id)
        test_point = None
        scene_map = None
        if tc.scene_node_id:
            tp_q = select(TestPoint).where(
                TestPoint.id == tc.scene_node_id,
                TestPoint.deleted_at.is_(None),
            )
            test_point = (await self.session.execute(tp_q)).scalar_one_or_none()

        if test_point:
            result["test_point"] = test_point
            sm_q = select(SceneMap).where(
                SceneMap.id == test_point.scene_map_id,
                SceneMap.deleted_at.is_(None),
            )
            scene_map = (await self.session.execute(sm_q)).scalar_one_or_none()

        result["scene_map"] = scene_map

        # Requirement
        req = await self.session.get(Requirement, tc.requirement_id)
        result["requirement"] = req if req and req.deleted_at is None else None

        # Iteration → Product
        if req and req.deleted_at is None:
            iteration = await self.session.get(Iteration, req.iteration_id)
            result["iteration"] = iteration if iteration and iteration.deleted_at is None else None

            if iteration and iteration.deleted_at is None:
                product = await self.session.get(Product, iteration.product_id)
                result["product"] = product if product and product.deleted_at is None else None
            else:
                result["product"] = None
        else:
            result["iteration"] = None
            result["product"] = None

        return result

    # ── Module path tree ───────────────────────────────────────────

    async def get_module_paths(self) -> list[dict]:
        """返回所有唯一 module_path 及其用例数量，构建为树形结构。

        返回格式：
        [
          {"path": "登录模块", "count": 12, "children": [
            {"path": "登录模块/手机号登录", "count": 7, "children": [...]},
            ...
          ]},
          ...
        ]
        """
        q = (
            select(TestCase.module_path, func.count(TestCase.id).label("cnt"))
            .where(TestCase.deleted_at.is_(None), TestCase.module_path.isnot(None))
            .group_by(TestCase.module_path)
            .order_by(TestCase.module_path)
        )
        result = await self.session.execute(q)
        rows = [(row.module_path, row.cnt) for row in result.all() if row.module_path]

        # 未分类用例数量（module_path 为 None 或空）
        uncategorized_q = select(func.count(TestCase.id)).where(
            TestCase.deleted_at.is_(None),
            or_(TestCase.module_path.is_(None), TestCase.module_path == ""),
        )
        uncategorized_count = (await self.session.execute(uncategorized_q)).scalar() or 0

        # 构建树形结构
        def build_tree(path_counts: list[tuple[str, int]]) -> list[dict]:
            tree: dict[str, dict] = {}
            for path, count in path_counts:
                parts = path.split("/")
                current = tree
                for depth, part in enumerate(parts):
                    full_path = "/".join(parts[: depth + 1])
                    if full_path not in current:
                        current[full_path] = {"path": full_path, "name": part, "count": 0, "_children": {}}
                    current[full_path]["count"] += count
                    current = current[full_path]["_children"]

            def to_list(nodes: dict) -> list[dict]:
                result_list = []
                for node in nodes.values():
                    children = to_list(node.pop("_children"))
                    node["children"] = children
                    result_list.append(node)
                return result_list

            return to_list(tree)

        tree = build_tree(rows)
        return [
            {"path": "__uncategorized__", "name": "未分类", "count": uncategorized_count, "children": []},
            *tree,
        ]

    # ── Internal helpers ───────────────────────────────────────────

    async def _create_version(self, tc: TestCase, *, change_reason: str | None = None) -> TestCaseVersion:
        snapshot = {
            "title": tc.title,
            "module_path": tc.module_path,
            "priority": tc.priority,
            "case_type": tc.case_type,
            "precondition": tc.precondition,
            "steps": tc.steps or [],
            "tags": tc.tags or [],
            "status": tc.status,
        }
        version = TestCaseVersion(
            test_case_id=tc.id,
            version=tc.version,
            snapshot=snapshot,
            change_reason=change_reason,
        )
        self.session.add(version)
        return version


# ── Folder Service ─────────────────────────────────────────────────


class FolderService:
    MAX_DEPTH = 3

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_folders(self) -> list:
        from app.modules.testcases.models import TestCaseFolder

        q = (
            select(TestCaseFolder)
            .where(TestCaseFolder.deleted_at.is_(None))
            .order_by(TestCaseFolder.level, TestCaseFolder.sort_order, TestCaseFolder.name)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_folder(self, folder_id: UUID):
        from app.modules.testcases.models import TestCaseFolder

        item = await self.session.get(TestCaseFolder, folder_id)
        if not item or item.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
        return item

    async def create_folder(self, name: str, parent_id: UUID | None = None):
        from app.modules.testcases.models import TestCaseFolder

        level = 1
        if parent_id:
            parent = await self.get_folder(parent_id)
            level = parent.level + 1
            if level > self.MAX_DEPTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"最多支持 {self.MAX_DEPTH} 级目录",
                )

        # Check duplicate sibling name
        dup_q = select(func.count()).where(
            TestCaseFolder.name == name,
            TestCaseFolder.parent_id == parent_id if parent_id else TestCaseFolder.parent_id.is_(None),
            TestCaseFolder.deleted_at.is_(None),
        )
        if (await self.session.execute(dup_q)).scalar() > 0:
            raise HTTPException(status_code=400, detail="同级目录下已存在同名目录")

        max_order_q = select(func.max(TestCaseFolder.sort_order)).where(
            TestCaseFolder.parent_id == parent_id if parent_id else TestCaseFolder.parent_id.is_(None),
            TestCaseFolder.deleted_at.is_(None),
        )
        max_order = (await self.session.execute(max_order_q)).scalar() or 0

        folder = TestCaseFolder(name=name, parent_id=parent_id, level=level, sort_order=max_order + 1)
        self.session.add(folder)
        await self.session.commit()
        await self.session.refresh(folder)
        return folder

    async def update_folder(self, folder_id: UUID, name: str | None = None, sort_order: int | None = None):
        from app.modules.testcases.models import TestCaseFolder

        folder = await self.get_folder(folder_id)
        if name is not None and name != folder.name:
            if not name.strip():
                raise HTTPException(status_code=400, detail="目录名称不能为空")
            name = name[:20]  # max 20 chars
            dup_q = select(func.count()).where(
                TestCaseFolder.name == name,
                TestCaseFolder.parent_id == folder.parent_id
                if folder.parent_id
                else TestCaseFolder.parent_id.is_(None),
                TestCaseFolder.id != folder_id,
                TestCaseFolder.deleted_at.is_(None),
            )
            if (await self.session.execute(dup_q)).scalar() > 0:
                raise HTTPException(status_code=400, detail="同级目录下已存在同名目录")
            folder.name = name
        if sort_order is not None:
            folder.sort_order = sort_order
        await self.session.commit()
        await self.session.refresh(folder)
        return folder

    async def delete_folder(self, folder_id: UUID) -> dict:
        """删除目录（含子目录和所有用例），全部进回收站。返回删除的用例数量。"""
        from datetime import UTC, datetime

        from app.modules.recycle.models import RecycleItem
        from app.modules.testcases.models import TestCaseFolder

        folder = await self.get_folder(folder_id)
        if folder.is_system:
            raise HTTPException(status_code=403, detail="系统目录不可删除")

        # Collect all folder IDs recursively (DFS)
        async def collect_folder_ids(fid: UUID) -> list[UUID]:
            ids = [fid]
            children_q = select(TestCaseFolder.id).where(
                TestCaseFolder.parent_id == fid,
                TestCaseFolder.deleted_at.is_(None),
            )
            children = (await self.session.execute(children_q)).scalars().all()
            for child_id in children:
                ids.extend(await collect_folder_ids(child_id))
            return ids

        all_folder_ids = await collect_folder_ids(folder_id)
        now = datetime.now(UTC)

        # Move all cases in these folders to recycle bin
        cases_q = select(TestCase).where(
            TestCase.folder_id.in_(all_folder_ids),
            TestCase.deleted_at.is_(None),
        )
        cases = (await self.session.execute(cases_q)).scalars().all()
        case_count = len(cases)

        for tc in cases:
            recycle = RecycleItem(
                object_type="test_case",
                object_id=tc.id,
                object_name=tc.title,
                object_snapshot={"case_id": tc.case_id, "title": tc.title, "folder_id": str(folder_id)},
                reason=f"随目录「{folder.name}」删除",
            )
            self.session.add(recycle)
            tc.deleted_at = now

        # Move all folders to recycle bin
        folders_q = select(TestCaseFolder).where(
            TestCaseFolder.id.in_(all_folder_ids),
            TestCaseFolder.deleted_at.is_(None),
        )
        folders = (await self.session.execute(folders_q)).scalars().all()
        for f in folders:
            recycle_f = RecycleItem(
                object_type="test_case_folder",
                object_id=f.id,
                object_name=f.name,
                object_snapshot={
                    "name": f.name,
                    "level": f.level,
                    "parent_id": str(f.parent_id) if f.parent_id else None,
                },
                reason="目录被删除",
            )
            self.session.add(recycle_f)
            f.deleted_at = now

        await self.session.commit()
        return {"deleted_case_count": case_count}

    async def move_cases(self, case_ids: list[UUID], folder_id: UUID | None) -> int:
        if folder_id:
            await self.get_folder(folder_id)  # validate exists
        q = select(TestCase).where(TestCase.id.in_(case_ids), TestCase.deleted_at.is_(None))
        result = await self.session.execute(q)
        cases = list(result.scalars().all())
        for tc in cases:
            tc.folder_id = folder_id
        await self.session.commit()
        return len(cases)

    async def get_case_count(self, folder_id: UUID) -> int:
        q = select(func.count()).where(TestCase.folder_id == folder_id, TestCase.deleted_at.is_(None))
        return (await self.session.execute(q)).scalar() or 0

    async def batch_reorder(self, orders: list[dict]) -> None:
        """批量更新同级目录排序。orders: [{id: UUID, sort_order: int}]"""
        from app.modules.testcases.models import TestCaseFolder

        for item in orders:
            q = select(TestCaseFolder).where(
                TestCaseFolder.id == item["id"],
                TestCaseFolder.deleted_at.is_(None),
            )
            folder = (await self.session.execute(q)).scalar_one_or_none()
            if folder:
                folder.sort_order = item["sort_order"]
        await self.session.commit()

    async def init_from_products(self) -> dict:
        """根据产品/迭代/需求层级自动生成三级系统目录。幂等：已存在则跳过。"""
        from app.modules.products.models import Iteration, Product, Requirement
        from app.modules.testcases.models import TestCaseFolder

        created = 0

        async def get_or_create(name: str, parent_id: UUID | None, level: int) -> UUID:
            nonlocal created
            q = select(TestCaseFolder).where(
                TestCaseFolder.name == name,
                TestCaseFolder.parent_id == parent_id if parent_id else TestCaseFolder.parent_id.is_(None),
                TestCaseFolder.deleted_at.is_(None),
            )
            existing = (await self.session.execute(q)).scalar_one_or_none()
            if existing:
                return existing.id
            f = TestCaseFolder(name=name, parent_id=parent_id, level=level, is_system=True, sort_order=0)
            self.session.add(f)
            await self.session.flush()
            created += 1
            return f.id

        products = (await self.session.execute(select(Product).where(Product.deleted_at.is_(None)))).scalars().all()

        for p in products:
            p_fid = await get_or_create(p.name, None, 1)
            iterations = (
                (
                    await self.session.execute(
                        select(Iteration).where(Iteration.product_id == p.id, Iteration.deleted_at.is_(None))
                    )
                )
                .scalars()
                .all()
            )
            for it in iterations:
                it_fid = await get_or_create(it.name, p_fid, 2)
                reqs = (
                    (
                        await self.session.execute(
                            select(Requirement).where(
                                Requirement.iteration_id == it.id, Requirement.deleted_at.is_(None)
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                for req in reqs:
                    await get_or_create(req.title, it_fid, 3)

        # Ensure "未分类" root folder exists
        await get_or_create("未分类", None, 1)
        # Mark 未分类 as system
        uncat_q = select(TestCaseFolder).where(
            TestCaseFolder.name == "未分类",
            TestCaseFolder.parent_id.is_(None),
            TestCaseFolder.deleted_at.is_(None),
        )
        uncat = (await self.session.execute(uncat_q)).scalar_one_or_none()
        if uncat:
            uncat.is_system = True

        await self.session.commit()
        return {"created": created}

    async def get_tree(self) -> list[dict]:
        folders = await self.list_folders()
        count_map: dict[UUID, int] = {}
        for f in folders:
            count_map[f.id] = await self.get_case_count(f.id)

        folder_map: dict[UUID | None, list] = {}
        for f in folders:
            pid = f.parent_id
            folder_map.setdefault(pid, []).append(f)

        def build(parent_id: UUID | None) -> list[dict]:
            children = folder_map.get(parent_id, [])
            return [
                {
                    "id": f.id,
                    "name": f.name,
                    "level": f.level,
                    "sort_order": f.sort_order,
                    "is_system": f.is_system,
                    "case_count": count_map.get(f.id, 0),
                    "children": build(f.id),
                }
                for f in children
            ]

        return build(None)
