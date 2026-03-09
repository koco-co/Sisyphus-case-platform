"use client";

import React, { useState, useEffect, useCallback } from "react";
import { LayoutTemplate, Plus, Trash2, Copy } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface Template {
  id: string;
  name: string;
  category: string;
  description: string | null;
  usage_count: number;
  status: string;
  created_at: string;
}

const categoryLabels: Record<string, string> = {
  functional: "功能测试",
  performance: "性能测试",
  security: "安全测试",
  compatibility: "兼容性测试",
};

const categoryColors: Record<string, string> = {
  functional: "pill-green",
  performance: "pill-amber",
  security: "pill-red",
  compatibility: "",
};

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [total, setTotal] = useState(0);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("functional");
  const [newDesc, setNewDesc] = useState("");

  const fetchTemplates = useCallback(async () => {
    const params = new URLSearchParams();
    if (categoryFilter) params.set("category", categoryFilter);
    try {
      const res = await fetch(`${API}/templates/?${params}`);
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (e) {
      console.error(e);
    }
  }, [categoryFilter]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const createTemplate = async () => {
    if (!newName.trim()) return;
    try {
      await fetch(`${API}/templates/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newName,
          category: newCategory,
          description: newDesc || null,
          template_content: {},
        }),
      });
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
      fetchTemplates();
    } catch (e) {
      console.error(e);
    }
  };

  const useTemplate = async (id: string) => {
    try {
      await fetch(`${API}/templates/${id}/use`, { method: "POST" });
      fetchTemplates();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteTemplate = async (id: string) => {
    if (!confirm("确定删除？")) return;
    await fetch(`${API}/templates/${id}`, { method: "DELETE" });
    fetchTemplates();
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 20, color: "var(--text)" }}>
          <LayoutTemplate size={24} style={{ marginRight: 8, verticalAlign: "middle" }} />
          用例模板库 ({total})
        </h2>
        <div style={{ display: "flex", gap: 8 }}>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{
              padding: "8px 12px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg2)",
              color: "var(--text)",
              fontSize: 13,
            }}
          >
            <option value="">全部分类</option>
            <option value="functional">功能测试</option>
            <option value="performance">性能测试</option>
            <option value="security">安全测试</option>
            <option value="compatibility">兼容性测试</option>
          </select>
          <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
            <Plus size={14} style={{ marginRight: 4 }} /> 新建模板
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="card" style={{ padding: 16, marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="模板名称"
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "var(--bg2)",
                color: "var(--text)",
                fontSize: 13,
                outline: "none",
              }}
            />
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "var(--bg2)",
                color: "var(--text)",
                fontSize: 13,
              }}
            >
              <option value="functional">功能测试</option>
              <option value="performance">性能测试</option>
              <option value="security">安全测试</option>
              <option value="compatibility">兼容性测试</option>
            </select>
          </div>
          <textarea
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="模板描述..."
            rows={3}
            style={{
              width: "100%",
              padding: "8px 12px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg2)",
              color: "var(--text)",
              fontSize: 13,
              resize: "vertical",
              outline: "none",
              marginBottom: 12,
            }}
          />
          <button className="btn btn-primary" onClick={createTemplate}>
            创建模板
          </button>
        </div>
      )}

      <div className="grid-3" style={{ gap: 16 }}>
        {templates.map((tpl) => (
          <div key={tpl.id} className="card card-hover" style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
              <h4 style={{ margin: 0, fontSize: 14, color: "var(--text)" }}>{tpl.name}</h4>
              <span className={`pill ${categoryColors[tpl.category] || ""}`} style={{ fontSize: 10 }}>
                {categoryLabels[tpl.category] || tpl.category}
              </span>
            </div>
            {tpl.description && (
              <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5, margin: "0 0 12px" }}>
                {tpl.description}
              </p>
            )}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>使用 {tpl.usage_count} 次</span>
              <div style={{ display: "flex", gap: 4 }}>
                <button
                  className="btn"
                  style={{ padding: "4px 10px", fontSize: 11 }}
                  onClick={() => useTemplate(tpl.id)}
                >
                  <Copy size={12} style={{ marginRight: 4 }} /> 使用
                </button>
                <button
                  onClick={() => deleteTemplate(tpl.id)}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", padding: 4 }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
        {templates.length === 0 && (
          <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--text-secondary)", gridColumn: "1 / -1" }}>
            <LayoutTemplate size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
            <p style={{ fontSize: 14 }}>暂无模板</p>
            <p style={{ fontSize: 12 }}>点击"新建模板"创建第一个测试用例模板</p>
          </div>
        )}
      </div>
    </div>
  );
}
