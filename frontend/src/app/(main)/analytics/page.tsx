"use client";

import React, { useState, useEffect } from "react";
import { BarChart3, PieChart, TrendingUp } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<any>({});
  const [priority, setPriority] = useState<any[]>([]);
  const [status, setStatus] = useState<any[]>([]);
  const [source, setSource] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/analytics/overview`).then((r) => r.json()).catch(() => ({})),
      fetch(`${API}/analytics/priority-distribution`).then((r) => r.json()).catch(() => []),
      fetch(`${API}/analytics/status-distribution`).then((r) => r.json()).catch(() => []),
      fetch(`${API}/analytics/source-distribution`).then((r) => r.json()).catch(() => []),
    ]).then(([ov, pr, st, sr]) => {
      setOverview(ov);
      setPriority(pr);
      setStatus(st);
      setSource(sr);
    });
  }, []);

  const colors = ["#00d9a3", "#f59e0b", "#ef4444", "#8b5cf6", "#3b82f6", "#ec4899"];
  const totalCases = priority.reduce((s, p) => s + p.count, 0) || 1;

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ margin: "0 0 24px", fontSize: 20, color: "var(--text)" }}>
        <BarChart3 size={24} style={{ marginRight: 8, verticalAlign: "middle" }} />
        质量分析看板
      </h2>

      <div className="grid-4" style={{ gap: 16, marginBottom: 24 }}>
        {[
          { label: "子产品", value: overview.product_count, color: "#3b82f6" },
          { label: "迭代", value: overview.iteration_count, color: "#8b5cf6" },
          { label: "需求", value: overview.requirement_count, color: "#f59e0b" },
          { label: "测试用例", value: overview.testcase_count, color: "#00d9a3" },
        ].map((s) => (
          <div key={s.label} className="card" style={{ padding: 20, textAlign: "center" }}>
            <div style={{ fontSize: 32, fontWeight: 700, color: s.color }}>{s.value || 0}</div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-3" style={{ gap: 16 }}>
        <div className="card" style={{ padding: 20 }}>
          <h4 style={{ margin: "0 0 16px", fontSize: 14, color: "var(--text)" }}>
            <PieChart size={16} style={{ marginRight: 8, verticalAlign: "middle" }} />
            优先级分布
          </h4>
          {priority.map((p, i) => (
            <div key={p.priority} style={{ marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span style={{ color: "var(--text)" }}>{p.priority}</span>
                <span style={{ color: "var(--text-secondary)" }}>{p.count}</span>
              </div>
              <div className="progress-bar"><div style={{ width: `${(p.count / totalCases) * 100}%`, background: colors[i % colors.length] }} /></div>
            </div>
          ))}
          {priority.length === 0 && <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>暂无数据</div>}
        </div>

        <div className="card" style={{ padding: 20 }}>
          <h4 style={{ margin: "0 0 16px", fontSize: 14, color: "var(--text)" }}>
            <TrendingUp size={16} style={{ marginRight: 8, verticalAlign: "middle" }} />
            状态分布
          </h4>
          {status.map((s, i) => (
            <div key={s.status} style={{ marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span style={{ color: "var(--text)" }}>{s.status}</span>
                <span style={{ color: "var(--text-secondary)" }}>{s.count}</span>
              </div>
              <div className="progress-bar"><div style={{ width: `${(s.count / totalCases) * 100}%`, background: colors[(i + 2) % colors.length] }} /></div>
            </div>
          ))}
          {status.length === 0 && <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>暂无数据</div>}
        </div>

        <div className="card" style={{ padding: 20 }}>
          <h4 style={{ margin: "0 0 16px", fontSize: 14, color: "var(--text)" }}>
            <BarChart3 size={16} style={{ marginRight: 8, verticalAlign: "middle" }} />
            来源分布
          </h4>
          {source.map((s, i) => (
            <div key={s.source} style={{ marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                <span style={{ color: "var(--text)" }}>{s.source === "ai" ? "AI 生成" : s.source === "manual" ? "手动创建" : s.source}</span>
                <span style={{ color: "var(--text-secondary)" }}>{s.count}</span>
              </div>
              <div className="progress-bar"><div style={{ width: `${(s.count / totalCases) * 100}%`, background: colors[(i + 4) % colors.length] }} /></div>
            </div>
          ))}
          {source.length === 0 && <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>暂无数据</div>}
        </div>
      </div>
    </div>
  );
}
