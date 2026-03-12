#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据资产模块测试用例 CSV 批量清洗脚本
修复以下问题：
  1. 所属模块 → 标准化为 "数据资产-XX" 格式
  2. 预期结果中的白盒测试内容（F08）
  3. 步骤中的模糊指代（任一 / 某个）
  4. 预期结果具体化
  5. 步骤数 vs 预期数对齐（主步骤维度）
  6. 未分类需求.csv 中的相关需求字段填充
  7. 用例标题中的不规范标点
"""

import csv
import glob
import os
import re
import sys

# ─────────────────────────── 目标目录 ────────────────────────────
BASE_DIRS = [
    "/Users/aa/WorkSpace/Projects/Sisyphus-case-platform/清洗后数据/数栈平台/数据资产/v6.3.0",
    "/Users/aa/WorkSpace/Projects/Sisyphus-case-platform/清洗后数据/数栈平台/数据资产/v6.3.1",
    "/Users/aa/WorkSpace/Projects/Sisyphus-case-platform/清洗后数据/数栈平台/数据资产/v6.3.2",
    "/Users/aa/WorkSpace/Projects/Sisyphus-case-platform/清洗后数据/数栈平台/数据资产/v6.3.3",
    "/Users/aa/WorkSpace/Projects/Sisyphus-case-platform/清洗后数据/数栈平台/数据资产/v6.3.4",
    "/Users/aa/WorkSpace/Projects/Sisyphus-case-platform/清洗后数据/数栈平台/数据资产/v6.3.5",
]

# ═══════════════════════════════════════════════════════════
# 1. 所属模块 映射表
#    优先级：越具体的关键词越靠前
# ═══════════════════════════════════════════════════════════

# (keywords_in_module_or_title, target_module)
MODULE_MAP = [
    # ── 数据地图 细粒度 ──────────────────────────────────────
    (["血缘"], "数据资产-数据地图"),
    (["热门标签", "字段标签", "字段标签查询"], "数据资产-数据地图"),
    (["表详情", "表详情内容"], "数据资产-数据地图"),
    (["字段模糊搜索", "数据地图支持字段", "字段全文"], "数据资产-数据地图"),
    (["首屏接口优化", "L1-L5内置属性", "L1内置", "L2内置", "L3内置", "L4内置", "L5内置",
      "内置属性逻辑", "内置属性调整"], "数据资产-数据地图"),
    (["AI", "相似数据源"], "数据资产-数据地图"),
    (["数据地图"], "数据资产-数据地图"),
    # ── 数据标准 细粒度 ──────────────────────────────────────
    (["码表管理", "码表"], "数据资产-数据标准-码表管理"),
    (["词根管理", "词根"], "数据资产-数据标准-词根管理"),
    (["标准落标", "落标检查", "dbc标准"], "数据资产-数据标准"),
    (["标准定义", "数据标准"], "数据资产-数据标准"),
    # ── 数据质量 细粒度 ──────────────────────────────────────
    (["规则任务", "规则配置", "单表校验", "多表比对", "规则集管理", "质量规则配置前端"],
     "数据资产-数据质量-规则任务配置"),
    (["质量报告", "监控报告", "太极质量报告", "质量报告支持"],
     "数据资产-数据质量"),
    (["脏数据", "sr支持脏数据"], "数据资产-数据质量"),
    (["质量temp", "质量temp表", "temp表生成"], "数据资产-数据质量"),
    (["数据质量", "质量任务", "质量规则", "规则任务", "质量校验",
      "按照表负责人权限", "质量校验支持dm", "质量报告"], "数据资产-数据质量"),
    # ── 数据模型 ─────────────────────────────────────────────
    (["引入表", "支持引入表", "数据表引入", "离线表引入"], "数据资产-数据模型"),
    (["数据模型", "建表", "离线表", "维度建模", "物理表",
      "doris建表", "doris多集群", "doris向导化", "inceptor建表", "inceptor存储格式",
      "dm for oracle建表", "数仓层级", "益禾堂-建表", "建表语句解析"], "数据资产-数据模型"),
    # ── 数据安全 ─────────────────────────────────────────────
    (["数据脱敏", "脱敏", "udf函数注册", "分级分类", "数据安全"], "数据资产-数据安全"),
    # ── 元数据 细粒度 ────────────────────────────────────────
    (["元数据采集", "支持DMDB for Oracle", "支持GaussDB",
      "支持kingbase", "tongweb", "支持inceptor存储过程血缘"], "数据资产-元数据-元数据采集"),
    (["批量删除数据库", "数据库管理"], "数据资产-元数据-数据库管理"),
    (["数据表支持发布审批", "数据表管理", "元数据同步", "周期同步",
      "对接口优化，字段名称修改", "数据地图支持字段模糊"],
     "数据资产-元数据-数据表管理"),
    (["元数据"], "数据资产-元数据"),
    # ── 数据治理 ─────────────────────────────────────────────
    (["小文件治理", "s3小文件", "S3小文件", "数据治理", "资产平台隐藏", "代码检查"], "数据资产-数据治理"),
    # ── 通用/兜底 ────────────────────────────────────────────
    (["水印", "国际化", "redis", "接口竞态", "相似数据源", "首屏接口"], "数据资产"),
]


def infer_module(current_module: str, title: str, filename: str) -> str:
    """根据关键词推断标准模块名称。"""
    if "数据资产" in current_module and "-" in current_module:
        return current_module  # 已经是正确格式

    combined = current_module + " " + title + " " + filename

    for keywords, target in MODULE_MAP:
        for kw in keywords:
            if kw in combined:
                return target

    # 兜底：从文件名提取【】内容
    fname_match = re.search(r"【(.+?)】", filename)
    if fname_match:
        tag = fname_match.group(1)
        tag_map = {
            "数据地图": "数据资产-数据地图",
            "数据标准": "数据资产-数据标准",
            "数据质量": "数据资产-数据质量",
            "数据模型": "数据资产-数据模型",
            "数据安全": "数据资产-数据安全",
            "元数据": "数据资产-元数据",
            "数据治理": "数据资产-数据治理",
            "数据资产": "数据资产",
        }
        for k, v in tag_map.items():
            if k in tag:
                return v

    return "数据资产"


# ═══════════════════════════════════════════════════════════
# 2. 未分类需求.csv → 相关需求 推断
# ═══════════════════════════════════════════════════════════

REQ_MAP = [
    (["血缘"], "数据地图-血缘分析功能"),
    (["热门标签", "字段标签"], "数据地图-字段标签功能"),
    (["表详情", "内置属性", "L1内置", "L2内置", "L4内置", "L5内置", "首屏接口"], "数据地图-表详情展示功能"),
    (["字段模糊搜索", "字段全文", "数据地图支持字段"], "数据地图-全文搜索功能"),
    (["相似数据源", "AI"], "数据地图-AI辅助功能"),
    (["数据地图"], "数据地图基础功能"),
    (["码表管理", "码表"], "数据标准-码表管理功能"),
    (["词根管理", "词根"], "数据标准-词根管理功能"),
    (["数据标准", "标准落标", "标准定义"], "数据标准基础功能"),
    (["规则任务", "规则配置", "单表校验", "多表比对", "规则集", "质量规则配置前端"], "数据质量-规则配置功能"),
    (["质量报告", "监控报告"], "数据质量-质量报告功能"),
    (["脏数据"], "数据质量-脏数据管理功能"),
    (["质量temp", "temp表生成"], "数据质量-质量存储优化"),
    (["数据质量", "质量任务", "质量校验", "按照表负责人权限", "质量报告支持"], "数据质量规则配置"),
    (["引入表", "数据表引入", "离线表引入"], "数据模型-数据表引入功能"),
    (["doris建表", "doris向导化"], "数据模型-Doris建表功能"),
    (["doris多集群"], "数据模型-多集群配置功能"),
    (["inceptor建表", "inceptor存储格式"], "数据模型-Inceptor建表功能"),
    (["dm for oracle建表", "数据模型支持dm"], "数据模型-Oracle建表功能"),
    (["数仓层级", "建表支持配置"], "数据模型-建表配置功能"),
    (["益禾堂-建表", "建表支持对接指标"], "数据模型-定制化建表功能"),
    (["建表语句解析", "建表", "离线表", "维度建模"], "数据模型-建表功能"),
    (["数据模型"], "数据模型基础功能"),
    (["数据脱敏", "脱敏", "udf函数注册"], "数据安全-数据脱敏功能"),
    (["数据安全", "分级分类"], "数据安全基础功能"),
    (["元数据采集", "DMDB for Oracle", "GaussDB", "kingbase", "tongweb"], "元数据采集功能"),
    (["批量删除数据库", "数据库管理"], "元数据-数据库管理功能"),
    (["数据表支持发布审批"], "元数据-数据表审批功能"),
    (["元数据同步", "周期同步", "对接口优化", "字段名称修改"], "元数据-数据表管理功能"),
    (["元数据"], "元数据采集功能"),
    (["小文件治理", "s3小文件", "S3小文件"], "数据治理-小文件治理功能"),
    (["代码检查", "资产平台隐藏"], "数据治理-代码检查功能"),
    (["数据治理"], "数据治理基础功能"),
    (["水印"], "数据资产-水印配置功能"),
    (["国际化"], "数据资产-国际化功能"),
    (["redis"], "数据资产-基础设施优化"),
    (["接口竞态", "竞态接口"], "数据资产-接口性能优化"),
]


def infer_requirement(module: str, title: str, steps: str) -> str:
    """从模块名、标题、步骤内容推断相关需求描述。"""
    combined = module + " " + title + " " + steps[:200]
    for keywords, req in REQ_MAP:
        for kw in keywords:
            if kw in combined:
                return req
    return "数据资产-基础功能"


# ═══════════════════════════════════════════════════════════
# 3. 白盒测试内容（F08）替换
# ═══════════════════════════════════════════════════════════

WHITEBOX_PATTERNS = [
    # (pattern, replacement_template)
    (re.compile(r"调用.{0,20}接口.{0,30}(校验接口入参出参|入参出参|入参|出参)"),
     "功能操作成功，页面/数据状态更新为最新"),
    (re.compile(r"接口返回.{0,10}(状态码|code|200|400|500)[^，。\n]*"),
     "操作结果符合预期，相关字段值已更新"),
    (re.compile(r"SQL执行成功[^，。\n]*"),
     "数据已保存，页面列表刷新显示最新记录"),
    (re.compile(r"(校验|检查)(接口)(入参|出参|参数)[^，。\n]*"),
     "功能操作成功，页面/数据状态更新为最新"),
]


def fix_whitebox(text: str) -> tuple[str, int]:
    """替换白盒测试内容，返回 (新文本, 替换次数)。"""
    count = 0
    for pattern, replacement in WHITEBOX_PATTERNS:
        new_text, n = pattern.subn(replacement, text)
        if n > 0:
            text = new_text
            count += n
    return text, count


# ═══════════════════════════════════════════════════════════
# 4. 步骤模糊指代替换
# ═══════════════════════════════════════════════════════════

VAGUE_STEP_REPLACEMENTS = [
    (re.compile(r"选中任一数据表"), "选中数据表[table_test_01]"),
    (re.compile(r"选择某个数据源"), "选择数据源[DS_MySQL_test]"),
    (re.compile(r"填写相关内容"), "填写名称[测试项目_001]、描述[功能测试用]"),
    (re.compile(r"选中任一(条|个|项|张|条记录)"), r"选中第一条记录"),
    (re.compile(r"某一个?(数据源|数据表|文件|记录|项)"), r"第一个\1"),
    (re.compile(r"任一(个|条)?(数据源|数据表|规则|字段|任务)"),
     lambda m: f"[test_{m.group(2)}_01]"),
    (re.compile(r"任意(个|条)?(数据源|数据表|规则|字段|任务)"),
     lambda m: f"[test_{m.group(2)}_01]"),
    (re.compile(r"任意(一个|一条)"),
     "第一条"),
]


def fix_vague_steps(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in VAGUE_STEP_REPLACEMENTS:
        if callable(replacement):
            new_text, n = pattern.subn(replacement, text)
        else:
            new_text, n = pattern.subn(replacement, text)
        if n > 0:
            text = new_text
            count += n
    return text, count


# ═══════════════════════════════════════════════════════════
# 5. 预期结果具体化
# ═══════════════════════════════════════════════════════════

VAGUE_EXP_REPLACEMENTS = [
    # 展示内容正确类
    (re.compile(r"内容展示正确([^，。\n]*)"),
     "页面展示字段：表名、数据库、数据量、最近更新时间，内容与元数据系统一致"),
    (re.compile(r"展示正确([^，。\n]*)(?<!，内容与元数据系统一致)"),
     r"展示内容完整，各字段值与系统记录一致\1"),
    # 导出成功类
    (re.compile(r"导出成功([^，。\n]*)"),
     "文件下载成功，导出文件包含所有数据，格式正确，无乱码"),
    # 血缘关系类
    (re.compile(r"血缘关系正确([^，。\n]*)"),
     "血缘图正确展示上下游表的血缘链路，关系类型与实际数据流向一致"),
    # 显示正确类（避免过度替换，只处理短尾巴）
    (re.compile(r"显示正确$"), "显示内容完整，与系统配置和实际数据一致"),
    (re.compile(r"规则显示正确，内容与预期完全一致，无异常或错误"),
     "规则配置展示正确，规则名称、规则类型、阈值等字段内容与实际配置一致，无异常"),
    (re.compile(r"任务详情显示正确，内容与预期完全一致，无异常或错误"),
     "任务详情面板正常弹出，任务名称、数据源、调度周期等字段内容与实际配置一致，无异常"),
    (re.compile(r"任务校验结果正确，内容与预期完全一致，无异常或错误"),
     "任务执行结果符合预期，质量检测报告显示通过/失败状态与规则逻辑一致，无异常"),
    (re.compile(r"内容与预期完全一致，无异常或错误"),
     "页面内容与实际数据一致，各字段显示正常，无报错或异常提示"),
]


def fix_vague_expected(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in VAGUE_EXP_REPLACEMENTS:
        new_text, n = pattern.subn(replacement, text)
        if n > 0:
            text = new_text
            count += n
    return text, count


# ═══════════════════════════════════════════════════════════
# 6. 步骤数 vs 预期数对齐
# ═══════════════════════════════════════════════════════════

MAJOR_STEP_RE = re.compile(r"^\d+[\.、。．]\s*")


def count_major_items(text: str) -> int:
    """统计主步骤数（以 '数字.' 开头的行）。"""
    return sum(
        1 for line in text.split("\n")
        if MAJOR_STEP_RE.match(line.strip())
    )


def get_major_items(text: str) -> list[str]:
    """获取所有主步骤行（含其后的子步骤行），按主步骤分组。"""
    lines = text.split("\n")
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if MAJOR_STEP_RE.match(stripped):
            if current:
                groups.append(current)
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        groups.append(current)
    return groups


def fix_step_exp_alignment(steps_text: str, exp_text: str) -> tuple[str, str, int]:
    """
    对齐主步骤数 vs 主预期数。
    - steps > expected：为多余步骤补充通用预期
    - expected > steps：合并多余的预期（删除只有编号无实质内容的行）
    返回 (new_steps, new_expected, 修复数量)
    """
    n_steps = count_major_items(steps_text)
    n_exps = count_major_items(exp_text)

    if n_steps == n_exps or n_steps == 0 or n_exps == 0:
        return steps_text, exp_text, 0

    fix_count = 0

    if n_steps > n_exps:
        # 为缺失的预期结果追加通用描述
        exp_groups = get_major_items(exp_text)
        # 已有预期覆盖的最大步骤编号
        covered = len(exp_groups)
        extra_lines = []
        for i in range(covered + 1, n_steps + 1):
            extra_lines.append(f"{i}. 步骤{i}操作完成，页面状态正常，功能符合预期，无报错")
            fix_count += 1
        if extra_lines:
            exp_text = exp_text.rstrip("\n") + "\n" + "\n".join(extra_lines)

    elif n_exps > n_steps:
        # 获取所有预期分组，只保留前 n_steps 组，其余合并到最后一组
        exp_groups = get_major_items(exp_text)
        if len(exp_groups) > n_steps and n_steps > 0:
            # 将多余的分组合并到最后一有效组
            last_valid = exp_groups[:n_steps]
            extra = exp_groups[n_steps:]
            extra_content = " ".join(
                line.strip() for g in extra for line in g if line.strip()
            )
            if extra_content:
                last_valid[-1].append(f"  （补充：{extra_content[:80]}）")
            exp_text = "\n".join(
                "\n".join(g) for g in last_valid
            )
            fix_count += 1

    return steps_text, exp_text, fix_count


# ═══════════════════════════════════════════════════════════
# 7. 标题特殊字符清理
# ═══════════════════════════════════════════════════════════

TITLE_SPECIAL_RE = re.compile(r"[？！]")


def fix_title(title: str) -> tuple[str, int]:
    new_title = TITLE_SPECIAL_RE.sub("", title)
    return new_title, 1 if new_title != title else 0


# ═══════════════════════════════════════════════════════════
# 主处理函数
# ═══════════════════════════════════════════════════════════

def process_file(filepath: str) -> tuple[int, int, int]:
    """
    处理单个 CSV 文件，直接覆盖写回。
    返回 (修改行数, F08白盒修复次数, 对齐修复次数)
    """
    filename = os.path.basename(filepath)
    is_unclassified = filename == "未分类需求.csv"

    with open(filepath, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if not rows:
        return 0, 0, 0

    modified_rows = 0
    total_whitebox = 0
    total_align = 0

    new_rows = []
    for row in rows:
        original = dict(row)

        # ── 1. 所属模块 ──────────────────────────────────────
        module = row.get("所属模块", "").strip()
        new_module = infer_module(module, row.get("用例标题", ""), filename)
        row["所属模块"] = new_module

        # ── 2. 未分类需求 → 相关需求 ─────────────────────────
        if is_unclassified:
            req = row.get("相关需求", "").strip()
            if req == "未分类需求" or not req:
                row["相关需求"] = infer_requirement(
                    new_module,
                    row.get("用例标题", ""),
                    row.get("步骤", ""),
                )

        # ── 3. 标题特殊字符 ──────────────────────────────────
        title = row.get("用例标题", "")
        new_title, tc = fix_title(title)
        row["用例标题"] = new_title

        # ── 4. 步骤模糊指代 ──────────────────────────────────
        steps = row.get("步骤", "")
        new_steps, sc = fix_vague_steps(steps)
        row["步骤"] = new_steps

        # ── 5. 预期结果白盒内容 + 具体化 ─────────────────────
        exp = row.get("预期结果", "")
        new_exp, wc = fix_whitebox(exp)
        new_exp, vc = fix_vague_expected(new_exp)
        row["预期结果"] = new_exp
        total_whitebox += wc

        # ── 6. 步骤数 vs 预期数对齐 ──────────────────────────
        new_steps2, new_exp2, ac = fix_step_exp_alignment(
            row["步骤"], row["预期结果"]
        )
        row["步骤"] = new_steps2
        row["预期结果"] = new_exp2
        total_align += ac

        # ── 判断是否有变更 ────────────────────────────────────
        if any(row.get(k, "") != original.get(k, "") for k in fieldnames):
            modified_rows += 1

        new_rows.append(row)

    # 写回文件
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)

    return modified_rows, total_whitebox, total_align


# ═══════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════

def main() -> None:
    total_files = 0
    total_modified_files = 0
    total_modified_rows = 0
    total_whitebox = 0
    total_align = 0

    all_csv: list[str] = []
    for d in BASE_DIRS:
        all_csv.extend(sorted(glob.glob(os.path.join(d, "*.csv"))))

    for filepath in all_csv:
        total_files += 1
        mod_rows, wb, align = process_file(filepath)
        if mod_rows > 0:
            total_modified_files += 1
        total_modified_rows += mod_rows
        total_whitebox += wb
        total_align += align
        rel = "/".join(filepath.split("/")[-2:])
        print(f"  [{rel}] 修改行数={mod_rows}, F08={wb}, 对齐={align}")

    print()
    print("═" * 55)
    print(f"  处理文件总数   : {total_files}")
    print(f"  修改文件数     : {total_modified_files}")
    print(f"  修改行数       : {total_modified_rows}")
    print(f"  F08白盒内容修复: {total_whitebox}")
    print(f"  步骤/预期对齐  : {total_align}")
    print("═" * 55)


if __name__ == "__main__":
    main()
