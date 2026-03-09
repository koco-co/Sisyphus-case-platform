"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Target, ClipboardList, Map, List, TreePine, Undo2, Loader2, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useSSEStream } from "@/hooks/useSSEStream";
import { useStreamStore } from "@/stores/stream-store";
import type { SceneMap, TestPoint } from "@/types/api";

/* ── Static fallback data ── */
const fallbackTestPoints = [
  { id: "TP-001", title: "正常自动保存触发", dot: "dot-green", cases: 3, checked: true, group: "正常流程" },
  { id: "TP-002", title: "手动保存优先级高于自动", dot: "dot-green", cases: 2, checked: true, group: "正常流程" },
  { id: "TP-003", title: "草稿恢复弹窗交互", dot: "dot-green", cases: 3, checked: true, group: "正常流程" },
  { id: "TP-004", title: "localStorage 暂存", dot: "dot-yellow", cases: 4, checked: false, group: "异常场景" },
  { id: "TP-005", title: "网络恢复后同步策略", dot: "dot-yellow", cases: 3, checked: false, group: "异常场景" },
  { id: "TP-006", title: "并发编辑冲突", dot: "dot-red", cases: 5, checked: false, group: "异常场景" },
  { id: "TP-007", title: "草稿存储上限", dot: "dot-red", cases: 3, checked: false, group: "边界值" },
  { id: "TP-008", title: "保存间隔边界值", dot: "dot-yellow", cases: 4, checked: false, group: "边界值" },
  { id: "TP-009", title: "只读用户权限边界", dot: "dot-red", cases: 2, checked: false, group: "权限 & 安全" },
  { id: "TP-010", title: "草稿可见范围", dot: "dot-gray", cases: 0, checked: false, group: "权限 & 安全" },
];
const fallbackGroups = [...new Set(fallbackTestPoints.map((t) => t.group))];

const steps = [
  { label: "需求录入", done: true },
  { label: "健康诊断", done: true },
  { label: "测试点确认", active: true },
  { label: "生成用例", done: false },
];

function priorityDot(p: string) {
  if (p === "P0") return "dot-red";
  if (p === "P1") return "dot-yellow";
  if (p === "P2") return "dot-green";
  return "dot-gray";
}

function SceneMapContent() {
  const searchParams = useSearchParams();
  const reqId = searchParams.get("reqId");
  const queryClient = useQueryClient();
  const { streamSSE } = useSSEStream();
  const { thinkingText, contentText, isStreaming } = useStreamStore();

  const { data: sceneMap, isLoading, error } = useQuery({
    queryKey: ["sceneMap", reqId],
    queryFn: () => apiClient<SceneMap>(`/scene-map/${reqId}`),
    enabled: !!reqId,
  });

  const realTestPoints: TestPoint[] = sceneMap?.test_points ?? [];
  const useStatic = !reqId || (!isLoading && realTestPoints.length === 0 && !error);

  const tpList = useStatic
    ? fallbackTestPoints.map((t) => ({ ...t, group_name: t.group, description: null, priority: "P1", status: "pending", estimated_cases: t.cases, scene_map_id: "", source: "manual", id: t.id, created_at: "", updated_at: "" } as TestPoint & { dot: string; checked: boolean; group: string }))
    : realTestPoints;

  const groups = useStatic
    ? fallbackGroups
    : [...new Set(realTestPoints.map((tp) => tp.group_name))];

  const handleGenerate = async () => {
    if (!reqId) return;
    try {
      await streamSSE(`/scene-map/${reqId}/generate`, {});
      queryClient.invalidateQueries({ queryKey: ["sceneMap", reqId] });
    } catch {
      /* stream error handled by store */
    }
  };

  const selectedTp = useStatic ? fallbackTestPoints[3] : realTestPoints[0];

  return (
    <div className="no-sidebar" style={{ padding: 0 }}>
      {/* Sub-nav progress */}
      <div style={{ display: "flex", alignItems: "center", gap: 24, padding: "12px 24px", background: "var(--bg1)", borderBottom: "1px solid var(--border)" }}>
        {steps.map((s, i) => (
          <div key={s.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 24, height: 24, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, fontFamily: "var(--font-mono)", background: s.done ? "var(--accent)" : s.active ? "var(--accent-d)" : "var(--bg3)", color: s.done ? "#000" : s.active ? "var(--accent)" : "var(--text3)", border: s.active ? "1px solid rgba(0,217,163,.4)" : "1px solid transparent" }}>
              {s.done ? "✓" : i + 1}
            </div>
            <span style={{ fontSize: 12.5, fontWeight: s.active ? 600 : 400, color: s.active ? "var(--accent)" : s.done ? "var(--text2)" : "var(--text3)" }}>{s.label}</span>
            {i < steps.length - 1 && <div style={{ width: 40, height: 1, background: s.done ? "var(--accent)" : "var(--border)", marginLeft: 8 }} />}
          </div>
        ))}
        <div className="spacer" />
        {reqId && (
          <button className="btn btn-sm btn-primary" onClick={handleGenerate} disabled={isStreaming}>
            {isStreaming ? <><Loader2 size={12} className="spin" /> 生成中...</> : <><Sparkles size={12} /> AI 生成测试点</>}
          </button>
        )}
        <button className="btn btn-sm"><Undo2 size={12} /> 返回诊断</button>
        <button className="btn btn-sm btn-primary">确认，进入用例生成 →</button>
      </div>

      {/* Content */}
      <div style={{ padding: 24 }}>
        <div className="topbar">
          <div>
            <div className="page-watermark">{reqId ? `${reqId.slice(0, 8)}… · 测试点确认` : "REQ-089 · 测试点确认"}</div>
            <h1>测试点确认</h1>
            <div className="sub">确认测试场景覆盖范围，调整粒度后进入用例生成</div>
          </div>
          <div className="spacer" />
          <button className="btn btn-sm">全选</button>
          <button className="btn btn-sm">反选</button>
        </div>

        {/* AI streaming output */}
        {(isStreaming || thinkingText || contentText) && (
          <div className="card" style={{ marginBottom: 16 }}>
            {thinkingText && (
              <details open={isStreaming && !contentText} style={{ marginBottom: 8 }}>
                <summary style={{ fontSize: 12, color: "var(--text3)", cursor: "pointer" }}>💭 AI 思考过程</summary>
                <pre style={{ fontSize: 12, color: "var(--text3)", whiteSpace: "pre-wrap", margin: "8px 0 0" }}>{thinkingText}</pre>
              </details>
            )}
            {contentText && (
              <div style={{ fontSize: 13, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                {contentText}
                {isStreaming && <span className="streaming-cursor" />}
              </div>
            )}
          </div>
        )}

        {isLoading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 48 }}><Loader2 size={24} className="spin" /></div>
        ) : error ? (
          <div className="card" style={{ color: "var(--red)", padding: 24 }}>加载失败: {String(error)}</div>
        ) : (
          <div className="three-col">
            {/* Left: Test Point Tree */}
            <div className="col-left">
              <div className="col-header">
                <Target size={14} /> 测试点列表
                <span className="mono" style={{ marginLeft: "auto", fontSize: 10, color: "var(--text3)" }}>{tpList.length} 个测试点</span>
              </div>
              <div style={{ padding: 10 }}>
                {groups.map((g) => (
                  <div key={g}>
                    <div style={{ fontSize: 10.5, color: "var(--text3)", fontFamily: "var(--font-mono)", margin: "8px 0 6px" }}>{useStatic ? g : g}</div>
                    {(useStatic
                      ? fallbackTestPoints.filter((t) => t.group === g)
                      : realTestPoints.filter((t) => t.group_name === g)
                    ).map((tp) => {
                      const dot = useStatic ? (tp as typeof fallbackTestPoints[0]).dot : priorityDot((tp as TestPoint).priority);
                      return (
                        <div key={tp.id} className="tp-item">
                          <span className={`scene-dot ${dot}`} />
                          <span style={{ flex: 1, fontSize: 12 }}>{tp.title}</span>
                          <span className="mono" style={{ fontSize: 10, color: "var(--text3)" }}>
                            ~{useStatic ? (tp as typeof fallbackTestPoints[0]).cases : (tp as TestPoint).estimated_cases}条
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>

            {/* Middle: Detail */}
            <div className="col-mid">
              <div className="col-header" style={{ background: "var(--bg)" }}>
                <ClipboardList size={14} /> 测试点详情
              </div>
              <div style={{ padding: 16 }}>
                {selectedTp ? (
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                      <span className={`scene-dot ${useStatic ? (selectedTp as typeof fallbackTestPoints[0]).dot : priorityDot((selectedTp as TestPoint).priority)}`} />
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{selectedTp.title}</span>
                      <span className="pill pill-amber">待确认</span>
                    </div>
                    {!useStatic && (selectedTp as TestPoint).description && (
                      <div style={{ fontSize: 12.5, color: "var(--text2)", lineHeight: 1.7, marginBottom: 12 }}>
                        {(selectedTp as TestPoint).description}
                      </div>
                    )}
                    {useStatic && (
                      <div style={{ fontSize: 12.5, color: "var(--text2)", lineHeight: 1.7, marginBottom: 12 }}>
                        当网络中断时，系统将未保存的草稿数据写入浏览器的 localStorage 进行暂存。
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ color: "var(--text3)", textAlign: "center", padding: 48 }}>选择测试点查看详情</div>
                )}
              </div>
            </div>

            {/* Right: Scene Map Overview */}
            <div className="col-right">
              <div className="col-header">
                <Map size={14} /> 场景地图
                <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
                  <button className="btn btn-ghost btn-sm" style={{ fontSize: 10 }}><List size={12} /> 列表</button>
                  <button className="btn btn-sm btn-primary" style={{ fontSize: 10 }}><TreePine size={12} /> 图形</button>
                </div>
              </div>
              <div style={{ padding: 10 }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, marginBottom: 12, textAlign: "center" }}>
                  <div style={{ padding: 6, background: "rgba(0,217,163,.08)", borderRadius: 5, border: "1px solid rgba(0,217,163,.2)" }}>
                    <div className="mono" style={{ fontSize: 16, fontWeight: 600, color: "var(--accent)" }}>{tpList.length}</div>
                    <div style={{ fontSize: 9.5, color: "var(--text3)" }}>测试点</div>
                  </div>
                  <div style={{ padding: 6, background: "rgba(245,158,11,.08)", borderRadius: 5, border: "1px solid rgba(245,158,11,.2)" }}>
                    <div className="mono" style={{ fontSize: 16, fontWeight: 600, color: "var(--amber)" }}>{groups.length}</div>
                    <div style={{ fontSize: 9.5, color: "var(--text3)" }}>分组</div>
                  </div>
                </div>
                {groups.map((g) => (
                  <div key={g}>
                    <div style={{ fontSize: 10.5, color: "var(--text3)", fontFamily: "var(--font-mono)", margin: "8px 0 6px" }}>{g}</div>
                    {(useStatic
                      ? fallbackTestPoints.filter((t) => t.group === g)
                      : realTestPoints.filter((t) => t.group_name === g)
                    ).map((tp) => {
                      const dot = useStatic ? (tp as typeof fallbackTestPoints[0]).dot : priorityDot((tp as TestPoint).priority);
                      return (
                        <div key={tp.id} className="scene-node">
                          <span className={`scene-dot ${dot}`} />
                          <span style={{ fontSize: 12, flex: 1 }}>{tp.title}</span>
                          <span className="mono" style={{ fontSize: 10, color: "var(--text3)" }}>
                            ~{useStatic ? (tp as typeof fallbackTestPoints[0]).cases : (tp as TestPoint).estimated_cases}条
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ))}
                <div style={{ marginTop: 12, padding: 8, background: "var(--bg2)", borderRadius: 6, border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 11, color: "var(--text3)" }}>预计生成用例总数</div>
                  <div className="mono" style={{ fontSize: 22, fontWeight: 600, margin: "2px 0" }}>
                    ~{useStatic ? 30 : realTestPoints.reduce((sum, tp) => sum + tp.estimated_cases, 0)} 条
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text3)" }}>确认所有测试点后方可生成</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SceneMapPage() {
  return (
    <Suspense fallback={<div style={{ display: "flex", justifyContent: "center", padding: 48 }}><Loader2 size={24} /></div>}>
      <SceneMapContent />
    </Suspense>
  );
}
