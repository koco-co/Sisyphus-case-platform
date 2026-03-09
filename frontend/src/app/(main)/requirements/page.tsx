"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Zap, FolderOpen, Calendar, Target, ClipboardList, FileText, Plus, Loader2, X } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Product, Iteration, Requirement } from "@/types/api";

/* ── Static fallback data ── */
const fallbackRequirements = [
  { id: "REQ-001", title: "用户数据源接入管理", status: "draft", priority: "P1", testPoints: 5, cases: 12 },
  { id: "REQ-002", title: "数据同步调度引擎", status: "reviewed", priority: "P0", testPoints: 8, cases: 24 },
  { id: "REQ-003", title: "实时数据流处理", status: "draft", priority: "P1", testPoints: 3, cases: 0 },
  { id: "REQ-004", title: "数据质量检测规则", status: "diagnosed", priority: "P2", testPoints: 6, cases: 18 },
  { id: "REQ-005", title: "元数据自动采集", status: "draft", priority: "P1", testPoints: 4, cases: 8 },
];

const statusMap: Record<string, { label: string; cls: string }> = {
  draft: { label: "草稿", cls: "pill-gray" },
  reviewed: { label: "已评审", cls: "pill-green" },
  diagnosed: { label: "已诊断", cls: "pill-blue" },
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export default function RequirementsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [selectedIterationId, setSelectedIterationId] = useState<string | null>(null);

  const { data: products, isLoading: productsLoading } = useQuery({
    queryKey: ["products"],
    queryFn: () => apiClient<Product[]>("/products"),
  });

  // Auto-select first product
  useEffect(() => {
    if (products?.length && !selectedProductId) setSelectedProductId(products[0].id);
  }, [products, selectedProductId]);

  const { data: iterations } = useQuery({
    queryKey: ["iterations", selectedProductId],
    queryFn: () => apiClient<Iteration[]>(`/products/${selectedProductId}/iterations`),
    enabled: !!selectedProductId,
  });

  // Auto-select first iteration
  useEffect(() => {
    if (iterations?.length && !selectedIterationId) setSelectedIterationId(iterations[0].id);
  }, [iterations, selectedIterationId]);

  const { data: requirements, isLoading: reqLoading, error: reqError } = useQuery({
    queryKey: ["requirements", selectedProductId, selectedIterationId],
    queryFn: () =>
      apiClient<Requirement[]>(
        `/products/${selectedProductId}/iterations/${selectedIterationId}/requirements`
      ),
    enabled: !!selectedProductId && !!selectedIterationId,
  });

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    if (!selectedIterationId) return;
    fd.set("iteration_id", selectedIterationId);

    setUploading(true);
    setUploadError(null);
    try {
      const res = await fetch(`${API_BASE}/products/upload-requirement`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) {
        const detail = await res.text().catch(() => res.statusText);
        throw new Error(`上传失败: ${detail}`);
      }
      dialogRef.current?.close();
      form.reset();
      queryClient.invalidateQueries({ queryKey: ["requirements"] });
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setUploading(false);
    }
  };

  const displayReqs = requirements ?? [];
  const useStatic = !selectedProductId || (!reqLoading && displayReqs.length === 0 && !reqError);

  return (
    <>
      {/* Upload modal */}
      <dialog ref={dialogRef} style={{ padding: 0, border: "1px solid var(--border)", borderRadius: 12, background: "var(--bg)", color: "var(--text)", maxWidth: 440, width: "100%" }}>
        <form onSubmit={handleUpload} style={{ padding: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>新建需求</h2>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => dialogRef.current?.close()}><X size={14} /></button>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 12, color: "var(--text2)", display: "block", marginBottom: 4 }}>需求标题</label>
            <input name="title" className="input" required placeholder="输入需求标题" style={{ width: "100%" }} />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, color: "var(--text2)", display: "block", marginBottom: 4 }}>需求文档 (.docx / .pdf / .md / .txt)</label>
            <input name="file" type="file" accept=".docx,.doc,.pdf,.md,.txt" required className="input" style={{ width: "100%" }} />
          </div>
          {uploadError && <div className="alert alert-red" style={{ marginBottom: 12, fontSize: 12 }}>{uploadError}</div>}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            <button type="button" className="btn" onClick={() => dialogRef.current?.close()}>取消</button>
            <button type="submit" className="btn btn-primary" disabled={uploading}>
              {uploading ? <><Loader2 size={12} className="spin" /> 上传中...</> : "上传并创建"}
            </button>
          </div>
        </form>
      </dialog>

      <div className="sidebar-panel">
        <div className="sb-section">
          <div className="sb-label">子产品</div>
          {productsLoading ? (
            <div className="sb-item"><Loader2 size={14} /> 加载中...</div>
          ) : products?.length ? (
            products.map((p) => (
              <div key={p.id} className={`sb-item${selectedProductId === p.id ? " active" : ""}`} onClick={() => { setSelectedProductId(p.id); setSelectedIterationId(null); }} style={{ cursor: "pointer" }}>
                <Zap size={14} />{p.name}
              </div>
            ))
          ) : (
            <>
              <div className="sb-item active"><Zap size={14} />离线开发平台<span className="sb-count">25</span></div>
              <div className="sb-item"><FolderOpen size={14} />数据资产管理<span className="sb-count">12</span></div>
            </>
          )}
        </div>
        <hr className="divider" style={{ margin: "4px 0" }} />
        <div className="sb-section">
          <div className="sb-label">迭代</div>
          {iterations?.length ? (
            iterations.map((it) => (
              <div key={it.id} className={`sb-item${selectedIterationId === it.id ? " active" : ""}`} onClick={() => setSelectedIterationId(it.id)} style={{ cursor: "pointer" }}>
                <Calendar size={14} />{it.name}<span className="sb-count">{it.status}</span>
              </div>
            ))
          ) : (
            <div className="sb-item"><Calendar size={14} />暂无迭代</div>
          )}
        </div>
        <hr className="divider" style={{ margin: "4px 0" }} />
        <div className="sb-section">
          <div className="sb-label">需求列表</div>
          {displayReqs.map((r) => (
            <div key={r.id} className="sb-item" style={{ cursor: "pointer" }} onClick={() => router.push(`/workbench?reqId=${r.id}`)}>
              <span className="sb-dot" style={{ background: r.status === "reviewed" ? "var(--accent)" : r.status === "diagnosed" ? "var(--blue)" : "var(--text3)" }} />
              <span style={{ flex: 1, fontSize: 12 }}>{r.title}</span>
              <span className="sb-count">{r.req_id}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="main-with-sidebar">
        <div className="topbar">
          <div>
            <div className="page-watermark">{products?.[0]?.name ?? "子产品"} · {iterations?.find((i) => i.id === selectedIterationId)?.name ?? "迭代"}</div>
            <h1>需求卡片</h1>
            <div className="sub">{useStatic ? fallbackRequirements.length : displayReqs.length} 条需求 · 选择需求查看详情</div>
          </div>
          <div className="spacer" />
          <button className="btn btn-primary" onClick={() => dialogRef.current?.showModal()}><Plus size={14} /> 新建需求</button>
        </div>

        {reqLoading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 48 }}><Loader2 size={24} className="spin" /></div>
        ) : reqError ? (
          <div className="card" style={{ color: "var(--red)", padding: 24 }}>加载需求失败: {String(reqError)}</div>
        ) : (
          <div className="grid-3">
            {(useStatic ? fallbackRequirements : displayReqs).map((r) => {
              const isReal = "id" in r && "req_id" in r;
              const reqId = isReal ? (r as Requirement).req_id : (r as typeof fallbackRequirements[0]).id;
              const title = r.title;
              const st = r.status;
              const statusInfo = statusMap[st] ?? { label: st, cls: "pill-gray" };

              return (
                <div
                  key={isReal ? (r as Requirement).id : reqId}
                  className="card card-hover"
                  style={{ cursor: "pointer" }}
                  onClick={() => {
                    if (isReal) router.push(`/workbench?reqId=${(r as Requirement).id}`);
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                    <span className="mono" style={{ fontSize: 11, color: "var(--accent)" }}>{reqId}</span>
                    <span className={`pill ${statusInfo.cls}`}>{statusInfo.label}</span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 8 }}>{title}</div>
                  <div style={{ display: "flex", gap: 12, fontSize: 11.5, color: "var(--text3)" }}>
                    <span><Target size={12} /> 测试点</span>
                    <span><ClipboardList size={12} /> 用例</span>
                  </div>
                  <div className="progress-bar" style={{ marginTop: 10, height: 3 }}>
                    <div className="progress-fill" style={{ width: "0%" }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div style={{ marginTop: 32 }}>
          <div className="sec-header">
            <span className="sec-title">需求详情预览</span>
            <span style={{ fontSize: 11.5, color: "var(--text3)" }}>选择需求查看完整内容</span>
          </div>
          <div className="card" style={{ minHeight: 300, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text3)" }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}><FileText size={36} /></div>
              <div>点击需求卡片进入工作台</div>
              <div style={{ fontSize: 11.5, marginTop: 4 }}>支持富文本编辑、前置条件标注、验收标准管理</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
