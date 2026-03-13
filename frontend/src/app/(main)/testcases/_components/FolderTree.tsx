'use client';

import type { DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import {
  closestCenter,
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  GripVertical,
  Inbox,
  Plus,
  Trash2,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, api } from '@/lib/api';

export interface FolderNode {
  id: string;
  name: string;
  level: number;
  sort_order: number;
  case_count: number;
  is_system: boolean;
  children: FolderNode[];
}

interface FolderTreeProps {
  selectedFolderId: string | null;
  totalCount: number;
  onSelect: (id: string | null, name?: string) => void;
  onCasesChanged?: () => void;
  refreshKey?: number;
}

interface ContextMenu {
  x: number;
  y: number;
  folderId: string;
  folderName: string;
}

interface InlineCreate {
  parentId: string | null;
  depth: number;
}

interface DeleteConfirm {
  folderId: string;
  folderName: string;
  caseCount: number;
}

// ── Sortable folder row ───────────────────────────────────────────

function SortableFolderItem({
  node,
  depth,
  selectedFolderId,
  editingId,
  editName,
  editError,
  inlineCreate,
  onSelect,
  onStartEdit,
  onEditChange,
  onEditSubmit,
  onEditCancel,
  onDeleteClick,
  onContextMenu,
  onInlineCreateConfirm,
  onInlineCreateCancel,
  onInlineCreateChange,
  inlineCreateName,
}: {
  node: FolderNode;
  depth: number;
  selectedFolderId: string | null;
  editingId: string | null;
  editName: string;
  editError: string;
  inlineCreate: InlineCreate | null;
  onSelect: (id: string | null, name?: string) => void;
  onStartEdit: (node: FolderNode) => void;
  onEditChange: (v: string) => void;
  onEditSubmit: () => void;
  onEditCancel: () => void;
  onDeleteClick: (node: FolderNode) => void;
  onContextMenu: (e: React.MouseEvent, node: FolderNode) => void;
  onInlineCreateConfirm: () => void;
  onInlineCreateCancel: () => void;
  onInlineCreateChange: (v: string) => void;
  inlineCreateName: string;
}) {
  const [expanded, setExpanded] = useState(depth === 0);
  const isSelected = selectedFolderId === node.id;
  const hasChildren = node.children.length > 0;
  const isEditing = editingId === node.id;
  const isSystem = node.is_system;

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: node.id,
    disabled: isSystem,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  const editInputRef = useRef<HTMLInputElement>(null);

  // Auto-focus edit input
  useEffect(() => {
    if (isEditing) {
      editInputRef.current?.focus();
      editInputRef.current?.select();
    }
  }, [isEditing]);

  // Is this the parent of the inline-create input? (needed to auto-expand)
  const showCreateInput =
    inlineCreate !== null && inlineCreate.parentId === node.id && inlineCreate.depth === depth + 1;

  const padLeft = 8 + depth * 14;

  return (
    <div ref={setNodeRef} style={style}>
      {/* Row */}
      {/* biome-ignore lint/a11y/noStaticElementInteractions: context menu on folder row */}
      <div
        className={`group relative flex items-center gap-1 rounded-md transition-all
          ${isSelected ? 'bg-sy-accent/10' : 'hover:bg-sy-bg-2'}
          ${isDragging ? 'ring-1 ring-sy-accent/40' : ''}
        `}
        style={{ paddingLeft: `${padLeft}px` }}
        onContextMenu={(e) => !isSystem && onContextMenu(e, node)}
      >
        {/* Drag handle */}
        {!isSystem && (
          <button
            type="button"
            {...attributes}
            {...listeners}
            className="shrink-0 opacity-0 group-hover:opacity-60 cursor-grab active:cursor-grabbing text-sy-text-3 p-0.5 bg-transparent border-0"
            tabIndex={-1}
          >
            <GripVertical className="w-3 h-3" />
          </button>
        )}
        {isSystem && <span className="w-4 shrink-0" />}

        {/* Expand toggle */}
        {hasChildren ? (
          <button
            type="button"
            className="shrink-0 text-sy-text-3 hover:text-sy-text-2 p-0.5 bg-transparent border-0"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded((v) => !v);
            }}
          >
            {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>
        ) : (
          <span className="w-4 shrink-0" />
        )}

        {/* Folder icon */}
        {isSystem ? (
          <Inbox
            className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-sy-accent' : 'text-sy-text-3'}`}
          />
        ) : expanded && hasChildren ? (
          <FolderOpen
            className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-sy-accent' : 'text-amber-400/70'}`}
          />
        ) : (
          <Folder
            className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-sy-accent' : 'text-amber-400/70'}`}
          />
        )}

        {/* Name / Edit input */}
        {isEditing ? (
          <div className="flex-1 min-w-0 pr-1">
            <input
              ref={editInputRef}
              value={editName}
              onChange={(e) => onEditChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onEditSubmit();
                if (e.key === 'Escape') onEditCancel();
              }}
              maxLength={20}
              className="w-full text-[12px] bg-sy-bg-2 border border-sy-accent/50 rounded px-1.5 py-0.5 text-sy-text outline-none focus:border-sy-accent"
            />
            {editError && (
              <p className="text-[10.5px] text-sy-danger mt-0.5 leading-tight">{editError}</p>
            )}
          </div>
        ) : (
          <button
            type="button"
            className={`flex-1 text-left text-[12.5px] truncate py-1.5 pr-1 ${
              isSelected ? 'text-sy-accent' : 'text-sy-text-2'
            }`}
            onClick={() => {
              onSelect(isSelected ? null : node.id, isSelected ? undefined : node.name);
              if (hasChildren) setExpanded(true);
            }}
            onDoubleClick={() => !isSystem && onStartEdit(node)}
          >
            {node.name.length > 18 ? `${node.name.slice(0, 18)}…` : node.name}
          </button>
        )}

        {/* Case count badge */}
        <span
          className={`font-mono text-[10.5px] shrink-0 pr-1 ${
            isSelected ? 'text-sy-accent' : 'text-sy-text-3'
          }`}
        >
          {node.case_count}
        </span>

        {/* Delete button (hover, non-system only) */}
        {!isSystem && !isEditing && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDeleteClick(node);
            }}
            className="shrink-0 opacity-0 group-hover:opacity-60 hover:!opacity-100 text-sy-danger p-0.5 rounded mr-1 bg-transparent border-0 transition-opacity"
            title="删除目录"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Children */}
      {(hasChildren || showCreateInput) && expanded && (
        <SortableFolderLevel
          nodes={node.children.filter((c) => !c.is_system)}
          systemNodes={node.children.filter((c) => c.is_system)}
          depth={depth + 1}
          parentId={node.id}
          selectedFolderId={selectedFolderId}
          editingId={editingId}
          editName={editName}
          editError={editError}
          inlineCreate={inlineCreate}
          onSelect={onSelect}
          onStartEdit={onStartEdit}
          onEditChange={onEditChange}
          onEditSubmit={onEditSubmit}
          onEditCancel={onEditCancel}
          onDeleteClick={onDeleteClick}
          onContextMenu={onContextMenu}
          onInlineCreateConfirm={onInlineCreateConfirm}
          onInlineCreateCancel={onInlineCreateCancel}
          onInlineCreateChange={onInlineCreateChange}
          inlineCreateName={inlineCreateName}
        />
      )}
    </div>
  );
}

// ── Sortable level (shares DndContext via lifting) ─────────────────

function SortableFolderLevel({
  nodes,
  systemNodes,
  depth,
  parentId,
  selectedFolderId,
  editingId,
  editName,
  editError,
  inlineCreate,
  onSelect,
  onStartEdit,
  onEditChange,
  onEditSubmit,
  onEditCancel,
  onDeleteClick,
  onContextMenu,
  onInlineCreateConfirm,
  onInlineCreateCancel,
  onInlineCreateChange,
  inlineCreateName,
}: {
  nodes: FolderNode[];
  systemNodes: FolderNode[];
  depth: number;
  parentId: string | null;
  selectedFolderId: string | null;
  editingId: string | null;
  editName: string;
  editError: string;
  inlineCreate: InlineCreate | null;
  onSelect: (id: string | null, name?: string) => void;
  onStartEdit: (node: FolderNode) => void;
  onEditChange: (v: string) => void;
  onEditSubmit: () => void;
  onEditCancel: () => void;
  onDeleteClick: (node: FolderNode) => void;
  onContextMenu: (e: React.MouseEvent, node: FolderNode) => void;
  onInlineCreateConfirm: () => void;
  onInlineCreateCancel: () => void;
  onInlineCreateChange: (v: string) => void;
  inlineCreateName: string;
}) {
  const padLeft = 8 + depth * 14;
  const isRootCreateHere = inlineCreate?.parentId === parentId && depth === inlineCreate?.depth;
  const showCreateInput = isRootCreateHere;
  const internalCreateRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showCreateInput) {
      setTimeout(() => internalCreateRef.current?.focus(), 30);
    }
  }, [showCreateInput]);

  return (
    <SortableContext items={nodes.map((n) => n.id)} strategy={verticalListSortingStrategy}>
      {nodes.map((child) => (
        <SortableFolderItem
          key={child.id}
          node={child}
          depth={depth}
          selectedFolderId={selectedFolderId}
          editingId={editingId}
          editName={editName}
          editError={editError}
          inlineCreate={inlineCreate}
          onSelect={onSelect}
          onStartEdit={onStartEdit}
          onEditChange={onEditChange}
          onEditSubmit={onEditSubmit}
          onEditCancel={onEditCancel}
          onDeleteClick={onDeleteClick}
          onContextMenu={onContextMenu}
          onInlineCreateConfirm={onInlineCreateConfirm}
          onInlineCreateCancel={onInlineCreateCancel}
          onInlineCreateChange={onInlineCreateChange}
          inlineCreateName={inlineCreateName}
        />
      ))}

      {/* Inline create input at this level */}
      {showCreateInput && (
        <div
          className="flex items-center gap-1.5 py-1"
          style={{ paddingLeft: `${padLeft + 20}px` }}
        >
          <Folder className="w-3.5 h-3.5 shrink-0 text-amber-400/60" />
          <input
            ref={internalCreateRef}
            value={inlineCreateName}
            onChange={(e) => onInlineCreateChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onInlineCreateConfirm();
              if (e.key === 'Escape') onInlineCreateCancel();
            }}
            maxLength={20}
            placeholder="目录名称"
            className="flex-1 text-[12px] bg-sy-bg-2 border border-sy-accent/50 rounded px-1.5 py-0.5 text-sy-text outline-none focus:border-sy-accent placeholder:text-sy-text-3"
          />
        </div>
      )}

      {/* System folders always at bottom */}
      {systemNodes.map((sys) => (
        <SortableFolderItem
          key={sys.id}
          node={sys}
          depth={depth}
          selectedFolderId={selectedFolderId}
          editingId={editingId}
          editName={editName}
          editError={editError}
          inlineCreate={inlineCreate}
          onSelect={onSelect}
          onStartEdit={onStartEdit}
          onEditChange={onEditChange}
          onEditSubmit={onEditSubmit}
          onEditCancel={onEditCancel}
          onDeleteClick={onDeleteClick}
          onContextMenu={onContextMenu}
          onInlineCreateConfirm={onInlineCreateConfirm}
          onInlineCreateCancel={onInlineCreateCancel}
          onInlineCreateChange={onInlineCreateChange}
          inlineCreateName={inlineCreateName}
        />
      ))}
    </SortableContext>
  );
}

// ── Main FolderTree ───────────────────────────────────────────────

export function FolderTree({
  selectedFolderId,
  totalCount,
  onSelect,
  onCasesChanged,
  refreshKey,
}: FolderTreeProps) {
  const [allNodes, setAllNodes] = useState<FolderNode[]>([]);
  const [loading, setLoading] = useState(true);

  // Inline rename state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editError, setEditError] = useState('');

  // Inline create state
  const [inlineCreate, setInlineCreate] = useState<InlineCreate | null>(null);
  const [inlineCreateName, setInlineCreateName] = useState('');
  const rootCreateInputRef = useRef<HTMLInputElement>(null);

  // Right-click context menu
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);
  const contextMenuRef = useRef<HTMLDivElement>(null);

  // Delete confirm dialog
  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirm | null>(null);
  const [deleting, setDeleting] = useState(false);

  // DnD - active drag item
  const [activeId, setActiveId] = useState<string | null>(null);

  // Node lookup map (flat)
  const nodeMap = useRef<Map<string, FolderNode>>(new Map());

  const fetchFolders = useCallback(() => {
    setLoading(true);
    api
      .get<FolderNode[]>('/testcases/folders/tree')
      .then((data) => {
        const nodes = Array.isArray(data) ? data : [];
        setAllNodes(nodes);
        // Build flat map
        const map = new Map<string, FolderNode>();
        const walk = (list: FolderNode[]) => {
          for (const n of list) {
            map.set(n.id, n);
            walk(n.children);
          }
        };
        walk(nodes);
        nodeMap.current = map;
      })
      .catch(() => setAllNodes([]))
      .finally(() => setLoading(false));
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: fetchFolders is stable callback
  useEffect(() => {
    fetchFolders();
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: fetchFolders is stable callback
  useEffect(() => {
    if (refreshKey !== undefined && refreshKey > 0) fetchFolders();
  }, [refreshKey]);

  // Close context menu on outside click
  useEffect(() => {
    if (!contextMenu) return;
    const handler = (e: MouseEvent) => {
      if (contextMenuRef.current && !contextMenuRef.current.contains(e.target as Node)) {
        setContextMenu(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [contextMenu]);

  // Inline rename handlers
  const handleStartEdit = (node: FolderNode) => {
    if (node.is_system) return;
    setEditingId(node.id);
    setEditName(node.name);
    setEditError('');
    setContextMenu(null);
  };

  const handleEditSubmit = async () => {
    if (!editingId) return;
    const name = editName.trim();
    if (!name) {
      setEditError('名称不能为空');
      return;
    }
    try {
      await api.patch(`/testcases/folders/${editingId}`, { name });
      setEditingId(null);
      setEditError('');
      fetchFolders();
    } catch (err) {
      if (err instanceof ApiError) {
        setEditError(err.detail || '操作失败');
      } else {
        setEditError('操作失败');
      }
    }
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditError('');
  };

  // Inline create handlers
  const handleNewFolder = () => {
    let parentId: string | null = null;
    let depth = 0;
    if (selectedFolderId) {
      const sel = nodeMap.current.get(selectedFolderId);
      if (sel) {
        if (sel.level >= 3) return; // max depth
        parentId = sel.id;
        depth = sel.level; // child depth = parent.level (1-indexed => 0-indexed)
      }
    }
    setInlineCreate({ parentId, depth });
    setInlineCreateName('');
    if (parentId === null) {
      setTimeout(() => rootCreateInputRef.current?.focus(), 50);
    }
  };

  const handleInlineCreateConfirm = async () => {
    const name = inlineCreateName.trim();
    if (!name) {
      setInlineCreate(null);
      return;
    }
    try {
      await api.post('/testcases/folders', {
        name,
        parent_id: inlineCreate?.parentId ?? null,
      });
      setInlineCreate(null);
      setInlineCreateName('');
      fetchFolders();
    } catch {
      setInlineCreate(null);
    }
  };

  const handleInlineCreateCancel = () => {
    setInlineCreate(null);
    setInlineCreateName('');
  };

  // Delete handlers
  const handleDeleteClick = (node: FolderNode) => {
    setContextMenu(null);
    if (node.case_count > 0) {
      setDeleteConfirm({ folderId: node.id, folderName: node.name, caseCount: node.case_count });
    } else {
      performDelete(node.id);
    }
  };

  const performDelete = async (folderId: string) => {
    setDeleting(true);
    try {
      await api.delete(`/testcases/folders/${folderId}`);
      if (selectedFolderId === folderId) onSelect(null);
      fetchFolders();
      onCasesChanged?.();
    } catch {
      // silent
    } finally {
      setDeleting(false);
      setDeleteConfirm(null);
    }
  };

  // Context menu handlers
  const handleContextMenu = (e: React.MouseEvent, node: FolderNode) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, folderId: node.id, folderName: node.name });
  };

  // DnD sensor (require 4px move to start)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  // Find which list a node belongs to (by parentId)
  const findParentId = (id: string): string | null => {
    const walk = (nodes: FolderNode[], parentId: string | null): string | null | undefined => {
      for (const n of nodes) {
        if (n.id === id) return parentId;
        const found = walk(n.children, n.id);
        if (found !== undefined) return found;
      }
      return undefined;
    };
    return walk(allNodes, null) ?? null;
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(String(event.active.id));
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const activeParent = findParentId(String(active.id));
    const overParent = findParentId(String(over.id));

    // Only allow same-level reorder
    if (activeParent !== overParent) return;

    // Find sibling list
    const getSiblings = (nodes: FolderNode[], pid: string | null): FolderNode[] => {
      if (pid === null) return nodes.filter((n) => !n.is_system);
      for (const n of nodes) {
        if (n.id === pid) return n.children.filter((c) => !c.is_system);
        const found = getSiblings(n.children, pid);
        if (found.length) return found;
      }
      return [];
    };

    const siblings = getSiblings(allNodes, activeParent);
    const activeIdx = siblings.findIndex((n) => n.id === String(active.id));
    const overIdx = siblings.findIndex((n) => n.id === String(over.id));
    if (activeIdx === -1 || overIdx === -1) return;

    // Reorder
    const reordered = [...siblings];
    const [moved] = reordered.splice(activeIdx, 1);
    reordered.splice(overIdx, 0, moved);

    const items = reordered.map((n, i) => ({ id: n.id, sort_order: i + 1 }));
    try {
      await api.post('/testcases/folders/reorder', { items });
      fetchFolders();
    } catch {
      // revert is handled by fetchFolders on next render
    }
  };

  const nonSystemRoots = allNodes.filter((n) => !n.is_system);
  const systemRoots = allNodes.filter((n) => n.is_system);

  // Is + button disabled?
  const selectedNode = selectedFolderId ? nodeMap.current.get(selectedFolderId) : null;
  const addDisabled = selectedNode ? selectedNode.level >= 3 : false;

  const activeNode = activeId ? nodeMap.current.get(activeId) : null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-sy-border shrink-0">
        <span className="text-[11.5px] font-semibold text-sy-text-3 uppercase tracking-wider">
          目录
        </span>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            handleNewFolder();
          }}
          disabled={addDisabled}
          title={addDisabled ? '最多支持 3 级目录' : '新建目录'}
          className="p-0.5 rounded text-sy-text-3 hover:text-sy-accent disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Tree content */}
      <div className="flex-1 overflow-y-auto py-1.5 px-1.5">
        {/* 全部用例 */}
        <button
          type="button"
          onClick={() => onSelect(null)}
          className={`w-full flex items-center gap-1.5 px-2 py-1.5 rounded-md text-left transition-all mb-0.5
            ${selectedFolderId === null ? 'bg-sy-accent/10 text-sy-accent' : 'text-sy-text-2 hover:bg-sy-bg-2 hover:text-sy-text'}
          `}
        >
          <span className="w-3 shrink-0" />
          <Folder
            className={`w-3.5 h-3.5 shrink-0 ${selectedFolderId === null ? 'text-sy-accent' : 'text-sy-text-3'}`}
          />
          <span className="flex-1 text-[12.5px]">全部用例</span>
          <span
            className={`font-mono text-[10.5px] shrink-0 ${selectedFolderId === null ? 'text-sy-accent' : 'text-sy-text-3'}`}
          >
            {totalCount}
          </span>
        </button>

        {loading ? (
          <div className="px-3 py-4 text-[11.5px] text-sy-text-3">加载目录...</div>
        ) : allNodes.length === 0 && !inlineCreate ? (
          <div className="px-3 py-4 text-[11.5px] text-sy-text-3">暂无目录，点击 + 新建</div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <SortableFolderLevel
              nodes={nonSystemRoots}
              systemNodes={systemRoots}
              depth={0}
              parentId={null}
              selectedFolderId={selectedFolderId}
              editingId={editingId}
              editName={editName}
              editError={editError}
              inlineCreate={inlineCreate}
              onSelect={onSelect}
              onStartEdit={handleStartEdit}
              onEditChange={setEditName}
              onEditSubmit={handleEditSubmit}
              onEditCancel={handleEditCancel}
              onDeleteClick={handleDeleteClick}
              onContextMenu={handleContextMenu}
              onInlineCreateConfirm={handleInlineCreateConfirm}
              onInlineCreateCancel={handleInlineCreateCancel}
              onInlineCreateChange={setInlineCreateName}
              inlineCreateName={inlineCreateName}
            />

            {/* Root-level inline create */}
            {inlineCreate?.parentId === null && (
              <div className="flex items-center gap-1.5 py-1 px-2">
                <Folder className="w-3.5 h-3.5 shrink-0 text-amber-400/60" />
                <input
                  ref={rootCreateInputRef}
                  value={inlineCreateName}
                  onChange={(e) => setInlineCreateName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleInlineCreateConfirm();
                    if (e.key === 'Escape') handleInlineCreateCancel();
                  }}
                  maxLength={20}
                  placeholder="目录名称"
                  className="flex-1 text-[12px] bg-sy-bg-2 border border-sy-accent/50 rounded px-1.5 py-0.5 text-sy-text outline-none focus:border-sy-accent placeholder:text-sy-text-3"
                />
              </div>
            )}

            <DragOverlay>
              {activeNode && (
                <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-md bg-sy-bg-3 border border-sy-border text-sy-text-2 shadow-lg text-[12.5px]">
                  <Folder className="w-3.5 h-3.5 text-amber-400/70" />
                  {activeNode.name}
                </div>
              )}
            </DragOverlay>
          </DndContext>
        )}
      </div>

      {/* Right-click context menu */}
      {contextMenu && (
        <div
          ref={contextMenuRef}
          role="menu"
          className="fixed z-50 min-w-[120px] bg-sy-bg-1 border border-sy-border rounded-md shadow-lg py-1"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button
            type="button"
            className="w-full px-3 py-1.5 text-left text-[12.5px] text-sy-text-2 hover:bg-sy-bg-2 hover:text-sy-text transition-colors"
            onClick={() => {
              const node = nodeMap.current.get(contextMenu.folderId);
              if (node) handleStartEdit(node);
              setContextMenu(null);
            }}
          >
            重命名
          </button>
          <button
            type="button"
            className="w-full px-3 py-1.5 text-left text-[12.5px] text-sy-danger hover:bg-sy-danger/10 transition-colors"
            onClick={() => {
              const node = nodeMap.current.get(contextMenu.folderId);
              if (node) handleDeleteClick(node);
              setContextMenu(null);
            }}
          >
            删除
          </button>
        </div>
      )}

      {/* Delete confirm dialog */}
      {deleteConfirm && (
        <>
          {/* biome-ignore lint/a11y/noStaticElementInteractions: backdrop overlay pattern */}
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={() => setDeleteConfirm(null)}
            onKeyDown={(e) => e.key === 'Escape' && setDeleteConfirm(null)}
          >
            <div
              role="dialog"
              aria-modal="true"
              className="bg-sy-bg-1 border border-sy-border rounded-[10px] p-5 max-w-sm w-full mx-4 shadow-xl"
              onClick={(e) => e.stopPropagation()}
              onKeyDown={(e) => e.stopPropagation()}
            >
              <h3 className="text-[14px] font-semibold text-sy-text mb-2">删除目录</h3>
              <p className="text-[12.5px] text-sy-text-2 leading-relaxed mb-4">
                该目录下有{' '}
                <span className="text-sy-warn font-semibold">{deleteConfirm.caseCount}</span>{' '}
                条用例，删除后用例将移入回收站，目录结构不可恢复，是否继续？
              </p>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setDeleteConfirm(null)}
                  className="px-3 py-1.5 text-[12.5px] text-sy-text-2 border border-sy-border rounded-md hover:bg-sy-bg-2 transition-colors"
                >
                  取消
                </button>
                <button
                  type="button"
                  disabled={deleting}
                  onClick={() => performDelete(deleteConfirm.folderId)}
                  className="px-3 py-1.5 text-[12.5px] text-white bg-sy-danger/80 hover:bg-sy-danger rounded-md disabled:opacity-50 transition-colors"
                >
                  {deleting ? '删除中...' : '确认删除'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
