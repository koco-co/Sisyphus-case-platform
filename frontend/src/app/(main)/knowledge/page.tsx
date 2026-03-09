"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Plus, Search, Trash2, FileText, Tag } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface KnowledgeDoc {
  id: string;
  title: string;
  doc_type: string;
  tags: any;
  source: string;
  version: number;
  status: string;
  created_at: string;
}

export default function KnowledgePage() {
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState("standard");
  const [newContent, setNewContent] = useState("");

  const fetchDocs = async () => {
    const params = new URLSearchParams();
    if (typeFilter) params.set("doc_type", typeFilter);
    try {
      const res = await fetch(`${API}/knowledge/?${params}`);
      if (res.ok) {
        const data = await res.json();
        setDocs(data.items || []);
        setTotal(data.total || 0);
      }
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchDocs(); }, [typeFilter]);

  const createDoc = async () => {
    if (!newTitle.trim()) return;
    try {
      await fetch(`${API}/knowledge/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle, doc_type: newType, content: newContent }),
      });
      setShowCreate(false);
      setNewTitle("");
      setNewContent("");
      fetchDocs();
    } catch (e) { console.error(e); }
  };

  const deleteDoc = async (id: string) => {
    if (!confirm("确定删除？")) return;
    await fetch(`${API}/knowledge/${id}`, { method: "DELETE" });
    fetchDocs();
  };

  const typeLabels: Record<string, string> = { standard: "标准规范", checklist: "检查清单", best_practice: "最佳实践", domain: "领域知识" };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 20, color: "var(--text)" }}>
          <BookOpen size={24} style={{ marginRight: 8, verticalAlign: "middle" }} />
          知识库 ({total})
        </h2>
        <div style={{ display: "flex", gap: 8 }}>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg2)", color: "var(--text)", fontSize: 13 }}>
            <option value="">全部类型</option>
            <option value="standard">标准规范</option>
            <option value="checklist">检查清单</option>
            <option value="best_practice">最佳实践</option>
            <option value="domain">领域知识</option>
          </select>
          <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}><Plus size={14} style={{ marginRight: 4 }} /> 新建</button>
        </div>
      </div>

      {showCreate && (
        <div className="card" style={{ padding: 16, marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
            <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder="文档标题" style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg2)", color: "var(--text)", fontSize: 13, outline: "none" }} />
            <select value={newType} onChange={(e) => setNewType(e.target.value)} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg2)", color: "var(--text)", fontSize: 13 }}>
              <option value="standard">标准规范</option>
              <option value="checklist">检查清单</option>
              <option value="best_practice">最佳实践</option>
              <option value="domain">领域知识</option>
            </select>
          </div>
          <textarea value={newContent} onChange={(e) => setNewContent(e.target.value)} placeholder="文档内容..." rows={4} style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg2)", color: "var(--text)", fontSize: 13, resize: "vertical", outline: "none", marginBottom: 12 }} />
          <button className="btn btn-primary" onClick={createDoc}>创建</button>
        </div>
      )}

      <div style={{ display: "grid", gap: 12 }}>
        {docs.map((doc) => (
          <div key={doc.id} className="card card-hover" style={{ padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <FileText size={16} style={{ color: "var(--accent)" }} />
                <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text)" }}>{doc.title}</span>
                <span className="pill pill-green" style={{ fontSize: 10 }}>{typeLabels[doc.doc_type] || doc.doc_type}</span>
              </div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                版本 v{doc.version} · {doc.created_at?.slice(0, 10)}
              </div>
            </div>
            <button onClick={() => deleteDoc(doc.id)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", padding: 4 }}><Trash2 size={14} /></button>
          </div>
        ))}
        {docs.length === 0 && <div className="card" style={{ padding: 24, textAlign: "center", color: "var(--text-secondary)" }}>暂无知识库文档</div>}
      </div>
    </div>
  );
}
