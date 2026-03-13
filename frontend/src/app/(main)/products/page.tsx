'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { toast } from 'sonner';

import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { EmptyState } from '@/components/ui/EmptyState';
import { FormDialog } from '@/components/ui/FormDialog';
import { FormField } from '@/components/ui/FormField';
import { Pagination } from '@/components/ui/Pagination';
import { SearchInput } from '@/components/ui/SearchInput';
import { TableSkeleton } from '@/components/ui/TableSkeleton';

/* ── Inline API client ── */

const apiClient = {
  async get<T>(url: string): Promise<T> {
    const res = await fetch(`http://localhost:8000/api${url}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async post<T>(url: string, data?: unknown): Promise<T> {
    const res = await fetch(`http://localhost:8000/api${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async patch<T>(url: string, data?: unknown): Promise<T> {
    const res = await fetch(`http://localhost:8000/api${url}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async delete(url: string): Promise<void> {
    const res = await fetch(`http://localhost:8000/api${url}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
  },
};

/* ── Types ── */

interface Product {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/* ── Page ── */

const PAGE_SIZE = 20;

export default function ProductsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchText, setSearchText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  // Dialog states
  const [createOpen, setCreateOpen] = useState(false);
  const [editItem, setEditItem] = useState<Product | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);

  // Form states
  const [formName, setFormName] = useState('');
  const [formSlug, setFormSlug] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const { data: products, isLoading } = useQuery<Product[]>({
    queryKey: ['products'],
    queryFn: () => apiClient.get('/products'),
  });

  const createMutation = useMutation({
    mutationFn: (values: { name: string; slug: string; description?: string }) =>
      apiClient.post('/products', values),
    onSuccess: () => {
      toast.success('子产品创建成功');
      closeCreateDialog();
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: () => toast.error('创建失败，请重试'),
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      ...data
    }: {
      id: string;
      name?: string;
      slug?: string;
      description?: string;
    }) => apiClient.patch(`/products/${id}`, data),
    onSuccess: () => {
      toast.success('更新成功');
      closeEditDialog();
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: () => toast.error('更新失败，请重试'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/products/${id}`),
    onSuccess: () => {
      toast.success('已删除');
      setDeleteTarget(null);
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: () => toast.error('删除失败'),
  });

  /* ── Helpers ── */

  const resetForm = () => {
    setFormName('');
    setFormSlug('');
    setFormDesc('');
    setFormErrors({});
  };

  const closeCreateDialog = () => {
    setCreateOpen(false);
    resetForm();
  };

  const closeEditDialog = () => {
    setEditItem(null);
    resetForm();
  };

  const openEditDialog = (p: Product) => {
    setFormName(p.name);
    setFormSlug(p.slug);
    setFormDesc(p.description ?? '');
    setFormErrors({});
    setEditItem(p);
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!formName.trim()) errs.name = '请输入名称';
    if (!formSlug.trim()) errs.slug = '请输入标识';
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleCreate = () => {
    if (!validate()) return;
    createMutation.mutate({
      name: formName.trim(),
      slug: formSlug.trim(),
      description: formDesc.trim() || undefined,
    });
  };

  const handleEdit = () => {
    if (!editItem || !validate()) return;
    updateMutation.mutate({
      id: editItem.id,
      name: formName.trim(),
      slug: formSlug.trim(),
      description: formDesc.trim() || undefined,
    });
  };

  /* ── Filtering & Pagination ── */

  const filtered = (products ?? []).filter(
    (p) =>
      !searchText ||
      p.name.toLowerCase().includes(searchText.toLowerCase()) ||
      p.slug.toLowerCase().includes(searchText.toLowerCase()),
  );

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  /* ── Form fields (shared between create/edit) ── */

  const renderFormFields = () => (
    <>
      <FormField label="名称" required error={formErrors.name}>
        <input
          className="input w-full"
          placeholder="例如：离线开发平台"
          value={formName}
          onChange={(e) => setFormName(e.target.value)}
        />
      </FormField>
      <FormField label="标识" required error={formErrors.slug}>
        <input
          className="input w-full"
          placeholder="例如：offline-dev"
          value={formSlug}
          onChange={(e) => setFormSlug(e.target.value)}
        />
      </FormField>
      <FormField label="描述">
        <textarea
          className="input w-full"
          rows={3}
          placeholder="项目简介（可选）"
          value={formDesc}
          onChange={(e) => setFormDesc(e.target.value)}
        />
      </FormField>
    </>
  );

  return (
    <div className="no-sidebar">
      <div className="max-w-[1200px] mx-auto">
        {/* ── Top bar ── */}
        <div className="topbar">
          <div>
            <div className="page-watermark">SISYPHUS · 子产品管理</div>
            <h1>子产品管理</h1>
            <div className="sub">管理所有子产品，点击名称查看迭代</div>
          </div>
          <div className="spacer" />
          <SearchInput
            value={searchText}
            onChange={(v) => {
              setSearchText(v);
              setCurrentPage(1);
            }}
            placeholder="搜索子产品..."
            className="w-[220px]"
          />
          <button
            type="button"
            className="btn btn-primary inline-flex items-center gap-1"
            onClick={() => {
              resetForm();
              setCreateOpen(true);
            }}
          >
            <Plus size={14} /> 新建
          </button>
        </div>

        {/* ── Table ── */}
        <div className="card p-0 overflow-hidden">
          {isLoading ? (
            <TableSkeleton rows={6} cols={4} />
          ) : filtered.length === 0 ? (
            <EmptyState
              title={searchText ? '未找到匹配的子产品' : '暂无子产品'}
              description={searchText ? '请尝试其他搜索关键词' : '点击右上角「新建」创建第一个子产品'}
            />
          ) : (
            <>
              <table className="tbl w-full">
                <thead>
                  <tr>
                    <th className="text-left">名称</th>
                    <th className="text-left">标识</th>
                    <th className="text-left">描述</th>
                    <th className="text-left w-[180px]">创建时间</th>
                    <th className="text-right w-[100px]">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {paginated.map((p) => (
                    <tr
                      key={p.id}
                      className="cursor-pointer hover:bg-bg2 transition-colors"
                      onClick={() => router.push(`/iterations?productId=${p.id}`)}
                    >
                      <td>
                        <button
                          type="button"
                          className="font-semibold text-accent hover:text-accent2 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/iterations?productId=${p.id}`);
                          }}
                        >
                          {p.name}
                        </button>
                      </td>
                      <td>
                        <span className="font-mono text-text3">{p.slug}</span>
                      </td>
                      <td>{p.description || <span className="text-text3">—</span>}</td>
                      <td>
                        <span className="font-mono">
                          {(() => {
                            try {
                              return new Date(p.created_at).toLocaleString('zh-CN');
                            } catch {
                              return p.created_at;
                            }
                          })()}
                        </span>
                      </td>
                      <td>
                        <div className="flex justify-end gap-1">
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              openEditDialog(p);
                            }}
                            title="编辑"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm text-red"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeleteTarget(p);
                            }}
                            title="删除"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="px-4 pb-3">
                <Pagination
                  current={currentPage}
                  total={filtered.length}
                  pageSize={PAGE_SIZE}
                  onChange={setCurrentPage}
                  showPageSizeChanger={false}
                  showQuickJumper={false}
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Create dialog ── */}
      <FormDialog
        open={createOpen}
        onClose={closeCreateDialog}
        onSubmit={handleCreate}
        title="新建子产品"
        submitText="新建"
        loading={createMutation.isPending}
      >
        {renderFormFields()}
      </FormDialog>

      {/* ── Edit dialog ── */}
      <FormDialog
        open={!!editItem}
        onClose={closeEditDialog}
        onSubmit={handleEdit}
        title="编辑子产品"
        submitText="保存"
        loading={updateMutation.isPending}
      >
        {renderFormFields()}
      </FormDialog>

      {/* ── Delete confirm ── */}
      <ConfirmDialog
        open={!!deleteTarget}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
        title="删除子产品"
        description={`确定要删除「${deleteTarget?.name}」吗？此操作不可撤销。`}
        confirmText="删除"
        variant="danger"
      />
    </div>
  );
}
