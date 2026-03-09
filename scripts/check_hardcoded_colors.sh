#!/usr/bin/env bash
# T-INT-08: 前端样式一致性检查 — 检测硬编码色值
#
# 使用方法:
#   chmod +x scripts/check_hardcoded_colors.sh
#   ./scripts/check_hardcoded_colors.sh
#
# 返回值: 0 = 无问题, 1 = 发现硬编码色值

set -euo pipefail

FRONTEND_DIR="${1:-frontend/src}"

echo "🔍 检查硬编码色值 — 目录: $FRONTEND_DIR"
echo "============================================="

VIOLATIONS=0

# 1. 检查 style={{ color: '#xxx' }} 或 style={{ backgroundColor: '#xxx' }}
echo ""
echo "── 检查 inline style 硬编码色值 ──"
if grep -rn --include="*.tsx" --include="*.ts" --include="*.jsx" \
    -E "style=\{.*#[0-9a-fA-F]{3,8}" "$FRONTEND_DIR" 2>/dev/null; then
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "  ✅ 无 inline style 硬编码色值"
fi

# 2. 检查 className="text-[#xxx]" / bg-[#xxx] / border-[#xxx] 等 Tailwind 任意值色值
echo ""
echo "── 检查 Tailwind 任意值硬编码色值 ──"
if grep -rn --include="*.tsx" --include="*.ts" --include="*.jsx" \
    -E "(text|bg|border|ring|shadow|fill|stroke)-\[#[0-9a-fA-F]{3,8}\]" "$FRONTEND_DIR" 2>/dev/null; then
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "  ✅ 无 Tailwind 任意值硬编码色值"
fi

# 3. 检查是否遗漏了 sy-* token（不在排除列表中的常见色值引用）
echo ""
echo "── 检查常见遗漏的品牌色硬编码 ──"
BRAND_COLORS=("#00d9a3" "#00b386" "#0d0f12" "#131619" "#1a1e24" "#212730" "#f59e0b" "#f43f5e" "#3b82f6" "#a855f7")
for color in "${BRAND_COLORS[@]}"; do
    matches=$(grep -rn --include="*.tsx" --include="*.ts" --include="*.jsx" \
        "$color" "$FRONTEND_DIR" 2>/dev/null | grep -v "tailwind.config" | grep -v "// " || true)
    if [ -n "$matches" ]; then
        echo "  ⚠️  发现品牌色硬编码 $color:"
        echo "$matches" | head -5
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [ "$VIOLATIONS" -eq 0 ]; then
    echo ""
    echo "  ✅ 无品牌色硬编码"
fi

# 汇总
echo ""
echo "============================================="
if [ "$VIOLATIONS" -gt 0 ]; then
    echo "❌ 发现 $VIOLATIONS 类硬编码色值问题"
    echo "   请使用 sy-* design token (如 text-sy-accent, bg-sy-bg-1)"
    exit 1
else
    echo "✅ 样式一致性检查通过"
    exit 0
fi
