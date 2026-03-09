"use client";

import React, { useState } from "react";
import { GitCompare, AlertTriangle, ArrowRight, History } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function DiffPage() {
  const [reqId, setReqId] = useState("");
  const [versionFrom, setVersionFrom] = useState(1);
  const [versionTo, setVersionTo] = useState(2);
  const [diffResult, setDiffResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const computeDiff = async () => {
    if (!reqId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/diff/${reqId}/compute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version_from: versionFrom, version_to: versionTo }),
      });
      if (res.ok) setDiffResult(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const loadHistory = async () => {
    if (!reqId) return;
    try {
      const res = await fetch(`${API}/diff/${reqId}/history`);
      if (res.ok) setHistory(await res.json());
    } catch (e) { console.error(e); }
  };

  const impactColor = (level: string) => {
    if (level === "high") return "#ef4444";
    if (level === "medium") return "#f59e0b";
    if (level === "low") return "#00d9a3";
    return "var(--text-secondary)";
  };

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ margin: "0 0 24px", fontSize: 20, color: "var(--text)" }}>
        <GitCompare size={24} style={{ marginRight: 8, verticalAlign: "middle" }} />
        需求变更 Diff
      </h2>

      <div className="card" style={{ padding: 16, marginBottom: 24, display: "flex", gap: 12, alignItems: "flex-end" }}>
        <div>
          <label style={{ fontSize: 12, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>需求 ID</label>
          <input value={reqId} onChange={(e) => setReqId(e.target.value)} placeholder="输入需求 UUID" style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg2)", color: "var(--text)", fontSize: 13, outline: "none", width: 280 }} />
        </div>
        <div>
          <label style={{ fontSize: 12, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>从版本</label>
          <input type="number" value={versionFrom} onChange={(e) => setVersionFrom(Number(e.target.value))} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg2)", color: "var(--text)", fontSize: 13, width: 80 }} />
        </div>
        <ArrowRight size={16} style={{ color: "var(--text-secondary)", marginBottom: 8 }} />
        <div>
          <label style={{ fontSize: 12, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>到版本</label>
          <input type="number" value={versionTo} onChange={(e) => setVersionTo(Number(e.target.value))} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg2)", color: "var(--text)", fontSize: 13, width: 80 }} />
        </div>
        <button className="btn btn-primary" onClick={computeDiff} disabled={loading}>{loading ? "分析中..." : "计算 Diff"}</button>
        <button className="btn" onClick={loadHistory}><History size={14} style={{ marginRight: 4 }} /> 历史</button>
      </div>

      {diffResult && (
        <div className="grid-3" style={{ gap: 16, marginBottom: 24 }}>
          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 8 }}>影响等级</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: impactColor(diffResult.impact_level) }}>{diffResult.impact_level?.toUpperCase()}</div>
          </div>
          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 8 }}>文本变更</div>
            <div style={{ display: "flex", gap: 16 }}>
              <span style={{ color: "#00d9a3", fontSize: 16, fontWeight: 600 }}>+{diffResult.text_diff?.additions || 0}</span>
              <span style={{ color: "#ef4444", fontSize: 16, fontWeight: 600 }}>-{diffResult.text_diff?.deletions || 0}</span>
            </div>
          </div>
          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 8 }}>受影响</div>
            <div style={{ fontSize: 13 }}>
              测试点: {diffResult.affected_test_points?.count || 0}，
              用例: {diffResult.affected_test_cases?.count || 0}
            </div>
          </div>
        </div>
      )}

      {diffResult?.text_diff?.diff_text && (
        <div className="card" style={{ padding: 16, marginBottom: 24 }}>
          <h4 style={{ margin: "0 0 12px", fontSize: 14, color: "var(--text)" }}>Diff 详情</h4>
          <pre className="mono" style={{ fontSize: 12, lineHeight: 1.6, overflow: "auto", maxHeight: 400, color: "var(--text)", background: "var(--bg2)", padding: 12, borderRadius: 8 }}>
            {diffResult.text_diff.diff_text}
          </pre>
        </div>
      )}

      {diffResult?.summary && (
        <div className="card" style={{ padding: 16, marginBottom: 24 }}>
          <h4 style={{ margin: "0 0 8px", fontSize: 14, color: "var(--text)" }}>摘要</h4>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>{diffResult.summary}</p>
        </div>
      )}

      {history.length > 0 && (
        <div className="card" style={{ padding: 16 }}>
          <h4 style={{ margin: "0 0 12px", fontSize: 14, color: "var(--text)" }}>变更历史</h4>
          <table className="tbl" style={{ width: "100%" }}>
            <thead><tr><th>版本</th><th>影响等级</th><th>摘要</th><th>时间</th></tr></thead>
            <tbody>
              {history.map((h: any) => (
                <tr key={h.id}>
                  <td>v{h.version_from} → v{h.version_to}</td>
                  <td><span style={{ color: impactColor(h.impact_level) }}>{h.impact_level}</span></td>
                  <td>{h.summary}</td>
                  <td style={{ fontSize: 12 }}>{h.created_at?.slice(0, 16)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
