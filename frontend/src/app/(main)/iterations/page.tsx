'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Calendar, Pencil, Plus, Trash2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { toast } from 'sonner';

import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { EmptyState } from '@/components/ui/EmptyState';
import { FormDialog } from '@/components/ui/FormDialog';
import { FormField } from '@/components/ui/FormField';
import { Pagination } from '@/components/ui/Pagination';
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

interface Iteration {
  id: string;
  product_id: string;
  name: string;
  start_date: string | null;
  end_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Product {
  id: string;
  name: string;
  slug: string;
}

const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  planning: { label: '规划中', cls: 'pill-gray' },
  active: { label: '进行中', cls: 'pill-green' },
  completed: { label: '已完成', cls: 'pill-blue' },
  archived: { label: '已归档', cls: 'pill-amber' },
};

const PAGE_SIZE = 20;

/* ── Page ── */

function IterationsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const productId = searchParams.get('productId');
  const queryClient = useQueryClient();
  const [currentPage, setCurrentPage] = useState(1);

  // Dialog states
  const [createOpen, setCreateOpen] = useState(false);
  const [editItem, setEditItem] = useState<Iteration | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Iteration | null>(null);

  // Form states
  const [formName, setFormName] = useState('');
  const [formStartDate, setFormStartDate] = useState('');
  const [formEndDate, setFormEndDate] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const { data: product } = useQuery<Product | null>({
    queryKey: ['product', productId],
    queryFn: () =>
      apiClient
        .get(`/products`)
        .then((list: unknown) => (list as Product[]).find((p) => p.id === productId) ?? null),
    enabled: !!productId,
  });

  const { data: iterations, isLoading } = useQuery<Iteration[]>({
    queryKey: ['iterations', productId],
    queryFn: () => apiClient.get(`/products/${productId}/iterations`),
    enabled: !!productId,
  });

  const createMutation = useMutation({
    mutationFn: (values: { name: string; product_id: string; start_date?: string; end_date?: string }) =>
      apiClient.post(`/products/${productId}/iterations`, values),
    onSuccess: () => {
      toast.success('迭代创建成功');
      closeCreateDialog();
      queryClient.invalidateQueries({ queryKey: ['iterations', productId] });
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
      start_date?: string;
      end_date?: string;
      status?: string;
    }) => apiClient.patch(`/products/iterations/${id}`, data),
    onSuccess: () => {
      toast.success('更新成功');
      closeEditDialog();
      queryClient.invalidateQueries({ queryKey: ['iterations', productId] });
    },
    onError: () => toast.error('更新失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/products/iterations/${id}`),
    onSuccess: () => {
      toast.success('已删除');
      setDeleteTarget(null);
      queryClient.invalidateQueries({ queryKey: ['iterations', productId] });
    },
    onError: () => toast.error('删除失败'),
  });

  /* ── Helpers ── */

  const resetForm = () => {
    setFormName('');
    setFormStartDate('');
    setFormEndDate('');
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

  const openEditDialog = (item: Iteration) => {
    setFormName(item.name);
    setFormStartDate(item.start_date ?? '');
    setFormEndDate(item.end_date ?? '');
    setFormErrors({});
    setEditItem(item);
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!formName.trim()) errs.name = '请输入迭代名称';
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleCreate = () => {
    if (!validate()) return;
    const payload: { name: string; product_id: string; start_date?: string; end_date?: string } = {
      name: formName.trim(),
      product_id: productId!,
    };
    if (formStartDate) payload.start_date = formStartDate;
    if (formEndDate) payload.end_date = formEndDate;
    createMutation.mutate(payload);
  };

  const handleEdit = () => {
    if (!editItem || !validate()) return;
    const payload: { id: string; name?: string; start_date?: string; end_date?: string } = {
      id: editItem.id,
      name: formName.trim(),
    };
    if (formStartDate) payload.start_date = formStartDate;
    if (formEndDate) payload.end_date = formEndDate;
    updateMutation.mutate(payload);
  };

  /* ── No product selected ── */

  if (!productId) {
    return (
      <div className="no-sidebar">
        <div className="max-w-[1200px] mx-auto pt-20">
          <EmptyState
            description="请先选择一个子产品"
            action={
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => router.push('/products')}
              >
                前往子产品管理
              </button>
            }
          />
        </div>
      </div>
    );
  }

  /* ── Pagination ── */

  const items = iterations ?? [];
  const paginated = items.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  /* ── Form fields (shared) ── */

  const renderFormFields = () => (
    <>
      <FormField label="迭代名称" required error={formErrors.name}>
        <input
          className="input w-full"
          placeholder="例如：Sprint 24-W05"
          value={formName}
          onChange={(e) => setFormName(e.target.value)}
        />
      </FormField>
      <FormField label="开始日期">
        <input
          type="date"
          className="input w-full"
          value={formStartDate}
          onChange={(e) => setFormStartDate(e.target.value)}
        />
      </FormField>
      <FormField label="结束日期">
        <input
          type="date"
          className="input w-full"
          value={formEndDate}
          onChange={(e) => setFormEndDate(e.target.value)}
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
            <div className="flex items-center gap-2 mb-1">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => router.push('/products')}
                title="返回子产品列表"
              >
                <ArrowLeft size={16} />
              </button>
              <div className="page-watermark">SISYPHUS · 迭代管理</div>
            </div>
            <h1 className="flex items-center gap-2">
              <Calendar size={20} />
              {product?.name ?? '子产品'} — 迭代列表
            </h1>
            <div className="sub">管理此子产品下的所有迭代，点击迭代名称查看需求</div>
          </div>
          <div className="spacer" />
          <button
            type="button"
            className="btn btn-primary inline-flex items-center gap-1"
            onClick={() => {
              resetForm();
              setCreateOpen(true);
            }}
          >
            <Plus size={14} /> 新建迭代
          </button>
        </div>

        {/* ── Table ── */}
        <div className="card p-0 overflow-hidden">
          {isLoading ? (
            <TableSkeleton rows={5} cols={5} />
          ) : items.length === 0 ? (
            <EmptyState
              title="暂无迭代"
              description="点击右上角「新建迭代」开始"
            />
          ) : (
            <>
              <table className="tbl w-full">
                <thead>
                  <tr>
                    <th className="text-left">迭代名称</th>
                    <th className="text-left w-[140px]">开始日期</th>
                    <th className="text-left w-[140px]">结束日期</th>
                    <th className="text-left w-[120px]">状态</th>
                    <th className="text-right w-[100px]">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {paginated.map((item) => {
                    const s = STATUS_MAP[item.status] ?? { label: item.status, cls: 'pill-gray' };
                    return (
                      <tr
                        key={item.id}
                        className="cursor-pointer hover:bg-bg2 transition-colors"
                        onClick={() => router.push(`/requirements?iterationId=${item.id}`)}
                      >
                        <td>
                          <button
                            type="button"
                            className="font-semibold text-accent hover:text-accent2 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/requirements?iterationId=${item.id}`);
                            }}
                          >
                            {item.name}
                          </button>
                        </td>
                        <td>
                          {item.start_date ? (
                            <span className="font-mono">{item.start_date}</span>
                          ) : (
                            <span className="text-text3">—</span>
                          )}
                        </td>
                        <td>
                          {item.end_date ? (
                            <span className="font-mono">{item.end_date}</span>
                          ) : (
                            <span className="text-text3">—</span>
                          )}
                        </td>
                        <td>
                          <span className={`pill ${s.cls}`}>{s.label}</span>
                        </td>
                        <td>
                          <div className="flex justify-end gap-1">
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                openEditDialog(item);
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
                                setDeleteTarget(item);
                              }}
                              title="删除"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              <div className="px-4 pb-3">
                <Pagination
                  current={currentPage}
                  total={items.length}
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
        title="新建迭代"
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
        title="编辑迭代"
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
        title="删除迭代"
        description={`确定要删除「${deleteTarget?.name}」吗？此操作不可撤销。`}
        confirmText="删除"
        variant="danger"
      />
    </div>
  );
}

export default function IterationsPage() {
  return (
    <Suspense
      fallback={
        <div className="no-sidebar">
          <div className="max-w-[1200px] mx-auto">
            <div className="card">
              <TableSkeleton rows={6} cols={5} />
            </div>
          </div>
        </div>
      }
    >
      <IterationsContent />
    </Suspense>
  );
}
