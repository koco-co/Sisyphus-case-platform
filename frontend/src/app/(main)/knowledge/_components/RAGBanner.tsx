'use client';

import { BookOpen, Brain, Sparkles, X } from 'lucide-react';
import { useState } from 'react';

export default function RAGBanner() {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 14,
        padding: '14px 18px',
        background: 'rgba(59, 130, 246, 0.06)',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        borderRadius: 10,
        marginBottom: 20,
        position: 'relative',
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 8,
          background: 'rgba(59, 130, 246, 0.12)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          color: 'var(--blue)',
        }}
      >
        <Brain size={18} />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--blue)',
            marginBottom: 4,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Sparkles size={13} />
          RAG 知识增强引擎
        </div>
        <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.7 }}>
          上传测试规范、检查清单、领域文档等知识文件，系统将自动进行向量化处理。在
          <span style={{ color: 'var(--accent)', fontWeight: 500 }}>用例生成</span>和
          <span style={{ color: 'var(--accent)', fontWeight: 500 }}>需求分析</span>
          时，AI 引擎会检索相关知识片段作为上下文，显著提升生成质量与准确度。
        </div>
        <div
          style={{
            display: 'flex',
            gap: 16,
            marginTop: 8,
            fontSize: 11,
            color: 'var(--text3)',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <BookOpen size={11} />
            支持 .md / .docx / .pdf / .txt
          </span>
          <span>自动分块 & 向量嵌入</span>
          <span>语义相似度检索</span>
        </div>
      </div>

      <button
        type="button"
        className="btn-ghost"
        onClick={() => setVisible(false)}
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--text3)',
          padding: 4,
          flexShrink: 0,
        }}
      >
        <X size={14} />
      </button>
    </div>
  );
}
