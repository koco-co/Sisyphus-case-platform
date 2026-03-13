'use client';

import { Archive, ClipboardList, Download, LayoutGrid, Table2, Trash, Upload } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import { SearchInput } from '@/components/ui/SearchInput';
import { StatCard } from '@/components/ui/StatCard';
import { CaseCard } from '@/components/workspace/CaseCard';
import { api } from '@/lib/api';
import { BatchActions } from './_components/BatchActions';
import { CaseDetailDrawer } from './_components/CaseDetailDrawer';
import { CaseEditForm } from './_components/CaseEditForm';
import { CaseTable } from './_components/CaseTable';
import { ChangeAlert } from './_components/ChangeAlert';
import { CleanCompareDrawer } from './_components/CleanCompareDrawer';
import { DiscardedRecordsModal } from './_components/DiscardedRecordsModal';
import ExportDialog from './_components/ExportDialog';
import { FilterToolbar } from './_components/FilterToolbar';
import { FolderTree } from './_components/FolderTree';
import { ImportDialog } from './_components/ImportDialog';
import { ImportedCasesTab } from './_components/ImportedCasesTab';
import type {
  CaseFilters,
  SortDirection,
  SortField,
  TestCaseDetail,
  TestCaseStep,
} from './_components/types';
import { sourceLabel, statusLabel, typeLabel } from './_components/types';

const PAGE_SIZE = 20;

interface ApiTestCaseStep {
  step?: number;
  no?: number;
  action: string;
  expected?: string;
  expected_result?: string;
}

interface ApiTestCaseDetail
  extends Omit<TestCaseDetail, 'steps' | 'status' | 'case_type' | 'source'> {
  steps: ApiTestCaseStep[];
  status: string;
  case_type: string;
  source: string;
}

const priorityRank: Record<string, number> = {
  P0: 0,
  P1: 1,
  P2: 2,
  P3: 3,
};

function normalizeStatus(status: string): string {
  if (status === 'active') return 'approved';
  if (status === 'pending_review') return 'review';
  return status;
}

function normalizeCaseType(caseType: string): string {
  return caseType === 'normal' ? 'functional' : caseType;
}

function normalizeSource(source: string): string {
  return source === 'ai' ? 'ai_generated' : source;
}

function normalizeSteps(steps: ApiTestCaseStep[]): TestCaseStep[] {
  return steps.map((step, index) => ({
    no: step.no ?? step.step ?? index + 1,
    action: step.action,
    expected_result: step.expected_result ?? step.expected ?? '',
  }));
}

function normalizeCase(testCase: ApiTestCaseDetail): TestCaseDetail {
  return {
    ...testCase,
    status: normalizeStatus(testCase.status),
    case_type: normalizeCaseType(testCase.case_type),
    source: normalizeSource(testCase.source),
    steps: normalizeSteps(testCase.steps ?? []),
  };
}

function toApiSteps(steps: TestCaseStep[]) {
  return steps.map((step, index) => ({
    step: step.no || index + 1,
    action: step.action,
    expected: step.expected_result,
  }));
}

function sortCases(cases: TestCaseDetail[], field: SortField | null, direction: SortDirection) {
  if (!field) return cases;

  return [...cases].sort((left, right) => {
    let result = 0;

    if (field === 'priority') {
      result = (priorityRank[left.priority] ?? 999) - (priorityRank[right.priority] ?? 999);
    } else if (field === 'updated_at') {
      result = new Date(left.updated_at).getTime() - new Date(right.updated_at).getTime();
    } else {
      result = String(left[field] ?? '').localeCompare(String(right[field] ?? ''), 'zh-CN');
    }

    return direction === 'asc' ? result : -result;
  });
}

function escapeCsv(value: string | number | null | undefined): string {
  const stringValue = String(value ?? '');
  if (/[",\n]/.test(stringValue)) {
    return `"${stringValue.replaceAll('"', '""')}"`;
  }
  return stringValue;
}

export default function TestCasesPage() {
  const router = useRouter();

  // ── Data ──
  const [cases, setCases] = useState<TestCaseDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showAlert, setShowAlert] = useState(false);

  // ── Global stats (全量统计，非页面级) ──
  const [globalStats, setGlobalStats] = useState<{
    total: number;
    approved: number;
    review: number;
    draft: number;
  }>({ total: 0, approved: 0, review: 0, draft: 0 });

  // ── 目录树 ──
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [selectedFolderName, setSelectedFolderName] = useState<string | null>(null);
  const [folderRefreshKey, setFolderRefreshKey] = useState(0);

  // ── Pagination ──
  const [page, setPage] = useState(1);

  // ── Search & Filters ──
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<CaseFilters>({
    priority: '',
    status: '',
    caseType: '',
    source: '',
    cleanStatus: '',
  });

  // ── Sorting ──
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // ── Selection ──
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // ── View mode ──
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table');

  // ── Drawer / Edit ──
  const [selectedCase, setSelectedCase] = useState<TestCaseDetail | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCaseDetail | null>(null);
  const [editFormOpen, setEditFormOpen] = useState(false);

  // ── Tab ──
  const [activeTab, setActiveTab] = useState<'ai' | 'imported'>('ai');

  // ── Clean Compare / Discarded ──
  const [compareOpen, setCompareOpen] = useState(false);
  const [discardedOpen, setDiscardedOpen] = useState(false);

  // ── Import / Export ──
  const [importOpen, setImportOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  // ── Delete confirmation ──
  const [deleteTarget, setDeleteTarget] = useState<{
    ids: string[];
    single: boolean;
  } | null>(null);

  // ── 拉取全量统计 ──
  const fetchStats = useCallback(async () => {
    try {
      const data = await api.get<{ total: number; by_status: { status: string; count: number }[] }>(
        '/testcases/stats',
      );
      const byStatus = data.by_status ?? [];
      const approved = byStatus
        .filter((s) => s.status === 'approved' || s.status === 'active')
        .reduce((acc, s) => acc + s.count, 0);
      const review = byStatus
        .filter((s) => s.status === 'review' || s.status === 'pending_review')
        .reduce((acc, s) => acc + s.count, 0);
      const draft = byStatus
        .filter((s) => s.status === 'draft')
        .reduce((acc, s) => acc + s.count, 0);
      setGlobalStats({ total: data.total ?? 0, approved, review, draft });
    } catch {
      // 忽略统计错误，不影响主列表
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // ── Fetch cases ──
  const fetchCases = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {
        page: String(page),
        page_size: String(PAGE_SIZE),
      };
      if (search) params.keyword = search;
      if (filters.priority) params.priority = filters.priority;
      if (filters.status) params.status = filters.status;
      if (filters.caseType) params.case_type = filters.caseType;
      if (filters.source) params.source = filters.source;
      if (selectedFolderId) params.folder_id = selectedFolderId;
      if (filters.cleanStatus) params.clean_status = filters.cleanStatus;

      const qs = new URLSearchParams(params).toString();
      const data = await api.get<{ items: ApiTestCaseDetail[]; total: number }>(`/testcases?${qs}`);
      const items = sortCases((data.items ?? []).map(normalizeCase), sortField, sortDirection);
      setCases(items);
      setTotal(data.total ?? 0);
    } catch (e) {
      console.error('Failed to fetch test cases:', e);
      setCases([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, search, filters, sortField, sortDirection, selectedFolderId]);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  // ── Handlers ──
  const handleFilterChange = <K extends keyof CaseFilters>(key: K, value: CaseFilters[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const handleClearFilters = () => {
    setFilters({ priority: '', status: '', caseType: '', source: '', cleanStatus: '' });
    setPage(1);
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleToggleSelectAll = () => {
    if (cases.every((c) => selectedIds.has(c.id))) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(cases.map((c) => c.id)));
    }
  };

  const handleRowClick = (tc: TestCaseDetail) => {
    setSelectedCase(tc);
    setDrawerOpen(true);
  };

  const handleEdit = (tc: TestCaseDetail) => {
    setEditingCase(tc);
    setEditFormOpen(true);
    setDrawerOpen(false);
  };

  const handleSave = async (data: {
    title: string;
    priority: string;
    status: string;
    case_type: string;
    precondition: string | null;
    module_path: string | null;
    steps: TestCaseStep[];
  }) => {
    if (!editingCase) return;
    try {
      await api.put(`/testcases/${editingCase.id}`, {
        ...data,
        steps: toApiSteps(data.steps),
      });
      setEditFormOpen(false);
      setEditingCase(null);
      await fetchCases();
      setFolderRefreshKey((k) => k + 1); // 目录树重新加载
    } catch (e) {
      console.error('Failed to save test case:', e);
      throw e; // 让 CaseEditForm 显示错误提示
    }
  };

  const handleDelete = async (ids: string[]) => {
    try {
      if (ids.length === 1) {
        await api.delete(`/testcases/${ids[0]}`);
      } else {
        await Promise.all(ids.map((id) => api.delete(`/testcases/${id}`)));
      }
      setSelectedIds(new Set());
      setDeleteTarget(null);
      setDrawerOpen(false);
      await Promise.all([fetchCases(), fetchStats()]);
    } catch (e) {
      console.error('Failed to delete:', e);
    }
  };

  const handleBatchStatusChange = async (status: string) => {
    try {
      await api.post('/testcases/batch-status', {
        case_ids: Array.from(selectedIds),
        status,
      });
      setSelectedIds(new Set());
      await Promise.all([fetchCases(), fetchStats()]);
    } catch (e) {
      console.error('Failed to batch update:', e);
    }
  };

  const handleBatchExport = async () => {
    try {
      const selectedCases = cases.filter((testCase) => selectedIds.has(testCase.id));
      if (selectedCases.length === 0) return;

      const header = [
        'case_id',
        'title',
        'priority',
        'status',
        'case_type',
        'source',
        'precondition',
        'steps',
      ];
      const rows = selectedCases.map((testCase) =>
        [
          testCase.case_id,
          testCase.title,
          testCase.priority,
          statusLabel[testCase.status] ?? testCase.status,
          typeLabel[testCase.case_type] ?? testCase.case_type,
          sourceLabel[testCase.source] ?? testCase.source,
          testCase.precondition ?? '',
          testCase.steps
            .map((step) => `${step.no}. ${step.action} => ${step.expected_result}`)
            .join(' | '),
        ]
          .map(escapeCsv)
          .join(','),
      );
      const blob = new Blob([`\uFEFF${[header.join(','), ...rows].join('\n')}`], {
        type: 'text/csv;charset=utf-8',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'testcases-export.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to export:', e);
    }
  };

  return (
    <div className="no-sidebar">
      {/* ── Header ── */}
      <div className="flex items-center gap-3 mb-5">
        <ClipboardList className="w-5 h-5 text-sy-accent" />
        <h1 className="font-display text-[20px] font-bold text-sy-text">用例管理中心</h1>
        <span className="text-[12px] text-sy-text-3">Test Case Management</span>
        <div className="flex-1" />
        <button
          type="button"
          onClick={() => setImportOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-sy-text-2 hover:text-sy-text border border-sy-border hover:border-sy-border-2 rounded-md transition-colors bg-sy-bg-2 hover:bg-sy-bg-3"
        >
          <Upload className="w-3.5 h-3.5" />
          导入
        </button>
        <button
          type="button"
          onClick={() => setExportOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-sy-text-2 hover:text-sy-text border border-sy-border hover:border-sy-border-2 rounded-md transition-colors bg-sy-bg-2 hover:bg-sy-bg-3"
        >
          <Download className="w-3.5 h-3.5" />
          导出
        </button>
        <button
          type="button"
          onClick={() => setDiscardedOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-sy-danger/70 hover:text-sy-danger border border-sy-danger/20 hover:border-sy-danger/40 rounded-md transition-colors bg-sy-danger/5 hover:bg-sy-danger/10"
        >
          <Trash className="w-3.5 h-3.5" />
          丢弃记录
        </button>
        <span className="font-mono text-[10px] text-sy-text-3 tracking-wider">M06 · TESTCASES</span>
      </div>

      {/* ── Tab Switcher ── */}
      <div className="flex items-center gap-0.5 mb-5 border-b border-sy-border">
        <button
          type="button"
          onClick={() => setActiveTab('ai')}
          className={`flex items-center gap-1.5 px-4 py-2 text-[13px] border-b-2 transition-colors -mb-px ${
            activeTab === 'ai'
              ? 'border-sy-accent text-sy-accent'
              : 'border-transparent text-sy-text-3 hover:text-sy-text-2'
          }`}
        >
          <ClipboardList className="w-3.5 h-3.5" />
          AI 生成用例
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('imported')}
          className={`flex items-center gap-1.5 px-4 py-2 text-[13px] border-b-2 transition-colors -mb-px ${
            activeTab === 'imported'
              ? 'border-sy-accent text-sy-accent'
              : 'border-transparent text-sy-text-3 hover:text-sy-text-2'
          }`}
        >
          <Archive className="w-3.5 h-3.5" />
          历史导入数据
        </button>
      </div>

      {/* ── Imported Cases Tab ── */}
      {activeTab === 'imported' && <ImportedCasesTab />}

      {/* ── AI Cases Tab ── */}
      {activeTab === 'ai' && (
        <>
          {/* ── Change Alert ── */}
          {showAlert && (
            <ChangeAlert
              count={0}
              onNavigate={() => router.push('/diff')}
              onDismiss={() => setShowAlert(false)}
            />
          )}

          {/* ── Stats (全量统计) ── */}
          <div className="grid grid-cols-4 gap-3 mb-5">
            <StatCard value={globalStats.total} label="总用例数" highlighted />
            <StatCard value={globalStats.approved} label="已通过" />
            <StatCard value={globalStats.review} label="评审中" />
            <StatCard value={globalStats.draft} label="草稿" />
          </div>

          {/* ── 双栏布局：左侧目录树 + 右侧用例列表 ── */}
          <div className="flex gap-4 min-h-0">
            {/* 左侧目录树 */}
            <div
              className="w-[220px] shrink-0 bg-sy-bg-1 border border-sy-border rounded-[10px] overflow-hidden flex flex-col"
              style={{ maxHeight: 'calc(100vh - 260px)', position: 'sticky', top: '12px' }}
            >
              <FolderTree
                selectedFolderId={selectedFolderId}
                totalCount={globalStats.total}
                refreshKey={folderRefreshKey}
                onSelect={(id, name) => {
                  setSelectedFolderId(id);
                  setSelectedFolderName(name ?? null);
                  setPage(1);
                  setSelectedIds(new Set());
                }}
                onCasesChanged={() => {
                  fetchCases();
                  fetchStats();
                  setFolderRefreshKey((k) => k + 1);
                }}
              />
            </div>

            {/* 右侧主内容 */}
            <div className="flex-1 min-w-0">
              {/* ── Search + Filters + View Toggle ── */}
              <div className="flex items-center gap-3 mb-4">
                <SearchInput
                  value={search}
                  onChange={(v) => {
                    setSearch(v);
                    setPage(1);
                  }}
                  placeholder="搜索用例编号或标题..."
                  className="w-[240px]"
                />
                <FilterToolbar
                  filters={filters}
                  onFilterChange={handleFilterChange}
                  onClearAll={handleClearFilters}
                />
                <div className="flex-1" />
                {selectedFolderId && (
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sy-bg-3 text-[11.5px] text-sy-text-2">
                    <span className="text-sy-text-3">目录：</span>
                    {selectedFolderName}
                    <button
                      type="button"
                      className="ml-1 text-sy-text-3 hover:text-sy-text"
                      onClick={() => {
                        setSelectedFolderId(null);
                        setSelectedFolderName(null);
                        setPage(1);
                      }}
                    >
                      ×
                    </button>
                  </span>
                )}
                <div className="flex items-center gap-1 p-0.5 bg-sy-bg-2 border border-sy-border rounded-md">
                  <button
                    type="button"
                    onClick={() => setViewMode('table')}
                    className={`p-1.5 rounded transition-colors ${
                      viewMode === 'table'
                        ? 'bg-sy-bg-3 text-sy-text'
                        : 'text-sy-text-3 hover:text-sy-text-2'
                    }`}
                    title="表格视图"
                  >
                    <Table2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('card')}
                    className={`p-1.5 rounded transition-colors ${
                      viewMode === 'card'
                        ? 'bg-sy-bg-3 text-sy-text'
                        : 'text-sy-text-3 hover:text-sy-text-2'
                    }`}
                    title="卡片视图"
                  >
                    <LayoutGrid className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* ── Batch Actions ── */}
              {selectedIds.size > 0 && (
                <BatchActions
                  selectedCount={selectedIds.size}
                  onStatusChange={handleBatchStatusChange}
                  onExport={handleBatchExport}
                  onDelete={() =>
                    setDeleteTarget({
                      ids: Array.from(selectedIds),
                      single: false,
                    })
                  }
                  onClearSelection={() => setSelectedIds(new Set())}
                />
              )}

              {/* ── Content ── */}
              {!loading && cases.length === 0 ? (
                <div className="bg-sy-bg-1 border border-sy-border rounded-[10px]">
                  <EmptyState
                    icon={<ClipboardList className="w-12 h-12" />}
                    title="暂无用例数据"
                    description={
                      selectedFolderId ? '该目录下暂无用例' : '当用例生成完成后，会自动出现在这里'
                    }
                  />
                </div>
              ) : viewMode === 'table' ? (
                <CaseTable
                  cases={cases}
                  selectedIds={selectedIds}
                  onToggleSelect={handleToggleSelect}
                  onToggleSelectAll={handleToggleSelectAll}
                  onRowClick={handleRowClick}
                  sortField={sortField}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                  loading={loading}
                />
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {loading ? (
                    <p className="col-span-2 py-16 text-center text-[12.5px] text-sy-text-3">
                      加载中...
                    </p>
                  ) : (
                    cases.map((tc) => (
                      <button
                        type="button"
                        key={tc.id}
                        className="cursor-pointer bg-transparent border-0 p-0 text-left"
                        onClick={() => handleRowClick(tc)}
                      >
                        <CaseCard
                          caseId={tc.case_id}
                          title={tc.title}
                          priority={tc.priority as 'P0' | 'P1' | 'P2' | 'P3'}
                          type={typeLabel[tc.case_type] ?? tc.case_type}
                          status={statusLabel[tc.status] ?? tc.status}
                          steps={tc.steps ?? []}
                          aiScore={tc.ai_score ?? undefined}
                          className="mb-0"
                        />
                      </button>
                    ))
                  )}
                </div>
              )}

              {/* ── Pagination ── */}
              <Pagination current={page} total={total} pageSize={PAGE_SIZE} onChange={setPage} />
            </div>
          </div>

          {/* ── Detail Drawer ── */}
          <CaseDetailDrawer
            testCase={selectedCase}
            open={drawerOpen}
            onClose={() => {
              setDrawerOpen(false);
              setSelectedCase(null);
            }}
            onEdit={handleEdit}
            onDelete={(id) => setDeleteTarget({ ids: [id], single: true })}
            onCompare={(tc) => {
              setDrawerOpen(false);
              setCompareOpen(true);
              setSelectedCase(tc);
            }}
          />

          {/* ── Edit Form ── */}
          <CaseEditForm
            testCase={editingCase}
            open={editFormOpen}
            onSave={handleSave}
            onCancel={() => {
              setEditFormOpen(false);
              setEditingCase(null);
            }}
          />

          {/* ── Delete Confirmation ── */}
          <ConfirmDialog
            open={deleteTarget !== null}
            title={
              deleteTarget?.single ? '删除用例' : `批量删除 ${deleteTarget?.ids.length ?? 0} 个用例`
            }
            description={
              deleteTarget?.single
                ? '此操作将软删除该用例，确认继续？'
                : `将软删除选中的 ${deleteTarget?.ids.length ?? 0} 个用例，确认继续？`
            }
            variant="danger"
            confirmText="删除"
            onConfirm={() => deleteTarget && handleDelete(deleteTarget.ids)}
            onCancel={() => setDeleteTarget(null)}
          />

          {/* ── Clean Compare Drawer ── */}
          <CleanCompareDrawer
            open={compareOpen}
            testCase={selectedCase}
            onClose={() => setCompareOpen(false)}
          />

          {/* ── Discarded Records Modal ── */}
          <DiscardedRecordsModal open={discardedOpen} onClose={() => setDiscardedOpen(false)} />

          {/* ── Import / Export Dialogs ── */}
          <ImportDialog
            open={importOpen}
            onClose={() => setImportOpen(false)}
            onImportComplete={fetchCases}
          />
          <ExportDialog
            open={exportOpen}
            onClose={() => setExportOpen(false)}
            selectedCount={selectedIds.size}
            currentFolder={selectedFolderName}
          />
        </>
      )}
    </div>
  );
}
