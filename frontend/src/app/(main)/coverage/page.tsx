"use client";

import React, { useState, useEffect } from "react";
import { Grid3x3, ChevronRight, BarChart3 } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface Product { id: string; name: string; }

export default function CoveragePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<string>("");
  const [coverageData, setCoverageData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/products/`)
      .then((r) => r.json())
      .then((data) => setProducts(Array.isArray(data) ? data : data.items || []))
      .catch(console.error);
  }, []);

  const loadCoverage = async (productId: string) => {
    setSelectedProduct(productId);
    setLoading(true);
    try {
      const res = await fetch(`${API}/coverage/product/${productId}`);
      if (res.ok) setCoverageData(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ margin: "0 0 24px", fontSize: 20, color: "var(--text)" }}>
        <Grid3x3 size={24} style={{ marginRight: 8, verticalAlign: "middle" }} />
        需求覆盖度矩阵
      </h2>

      <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
        {products.map((p) => (
          <button key={p.id} className={`btn ${selectedProduct === p.id ? "btn-primary" : ""}`} onClick={() => loadCoverage(p.id)}>
            {p.name}
          </button>
        ))}
      </div>

      {loading && <div style={{ textAlign: "center", padding: 40, color: "var(--text-secondary)" }}>加载中...</div>}

      {coverageData?.iterations && (
        <div style={{ display: "grid", gap: 16 }}>
          {coverageData.iterations.map((iter: any) => (
            <div key={iter.iteration_id} className="card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <h4 style={{ margin: 0, fontSize: 14, color: "var(--text)" }}>{iter.iteration_name}</h4>
                <div style={{ display: "flex", gap: 12, fontSize: 12 }}>
                  <span>需求: {iter.requirement_count}</span>
                  <span>用例: {iter.testcase_count}</span>
                  <span style={{ color: iter.uncovered_count > 0 ? "#ef4444" : "#00d9a3" }}>未覆盖: {iter.uncovered_count}</span>
                </div>
              </div>
              <div className="progress-bar" style={{ height: 8, marginBottom: 8 }}>
                <div style={{ width: `${iter.coverage_rate}%`, background: iter.coverage_rate >= 80 ? "#00d9a3" : iter.coverage_rate >= 50 ? "#f59e0b" : "#ef4444" }} />
              </div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>覆盖率: <span style={{ fontWeight: 600, color: "var(--text)" }}>{iter.coverage_rate}%</span></div>
            </div>
          ))}
        </div>
      )}

      {!coverageData && !loading && (
        <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--text-secondary)" }}>
          <Grid3x3 size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
          <p style={{ fontSize: 14 }}>选择产品查看覆盖度数据</p>
        </div>
      )}
    </div>
  );
}
