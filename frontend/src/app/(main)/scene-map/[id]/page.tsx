'use client';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { StatusPill, ThinkingStream, ProgressBar } from '@/components/ui';
import { useSSEStream } from '@/hooks/useSSEStream';
import { useStreamStore } from '@/stores/stream-store';
import { apiClient } from '@/lib/api-client';

interface TestPoint {
  id: string;
  scene_map_id: string;
  group_name: string;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  estimated_cases: number;
  source: string;
}

interface SceneMapData {
  id: string;
  requirement_id: string;
  status: string;
  test_points: TestPoint[];
}

const groupOrder = ['正常流程', '异常场景', '边界值', '权限安全'];
const groupIcons: Record<string, string> = { '正常流程': '✅', '异常场景': '⚠️', '边界值': '🔲', '权限安全': '🔒' };

export default function SceneMapPage() {
  const { id } = useParams<{ id: string }>();
  const { streamSSE } = useSSEStream();
  const { thinkingText, contentText, isStreaming } = useStreamStore();
  const [selectedTP, setSelectedTP] = useState<TestPoint | null>(null);
  const queryClient = useQueryClient();

  const { data: sceneMap } = useQuery({
    queryKey: ['scene-map', id],
    queryFn: () => apiClient<SceneMapData>(`/scene-map/${id}`),
  });

  const confirmMutation = useMutation({
    mutationFn: (tpId: string) => apiClient(`/scene-map/test-points/${tpId}`, { method: 'PATCH', body: JSON.stringify({ status: 'confirmed' }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scene-map', id] }),
  });

  async function generateTestPoints() {
    await streamSSE(`/scene-map/${id}/generate`, {});
    queryClient.invalidateQueries({ queryKey: ['scene-map', id] });
  }

  const testPoints = sceneMap?.test_points ?? [];
  const groups = groupOrder.filter((g) => testPoints.some((tp) => tp.group_name === g));
  const otherGroups = [...new Set(testPoints.map((tp) => tp.group_name))].filter((g) => !groupOrder.includes(g));
  const allGroups = [...groups, ...otherGroups];

  const totalEstimated = testPoints.reduce((sum, tp) => sum + tp.estimated_cases, 0);
  const confirmedCount = testPoints.filter((tp) => tp.status === 'confirmed').length;

  return (
    <div className="p-6 h-[calc(100vh-0px)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="font-display font-bold text-[20px]">测试点确认</h1>
          <div className="text-text3 text-[12px] mt-1">需求 ID: {id}</div>
        </div>
        <button type="button" onClick={generateTestPoints} disabled={isStreaming} className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-[12.5px] font-semibold bg-accent text-black disabled:opacity-50">
          {isStreaming ? '⏳ 生成中...' : '🤖 AI 生成测试点'}
        </button>
      </div>

      <div className="flex-1 grid grid-cols-[260px_1fr_300px] gap-4 min-h-0">
        {/* Left: Test point list */}
        <div className="bg-bg1 border border-border rounded-[10px] p-3 overflow-y-auto">
          <div className="text-[12px] font-semibold text-text2 mb-3">{testPoints.length} 个测试点</div>
          {allGroups.map((group) => (
            <div key={group} className="mb-3">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-text3 uppercase tracking-wide mb-1.5 px-1">
                <span>{groupIcons[group] ?? '📌'}</span>
                <span>{group}</span>
                <span className="font-mono ml-auto">{testPoints.filter((tp) => tp.group_name === group).length}</span>
              </div>
              {testPoints.filter((tp) => tp.group_name === group).map((tp) => (
                <div
                  key={tp.id}
                  onClick={() => setSelectedTP(tp)}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-[12px] mb-0.5 transition-all border ${
                    selectedTP?.id === tp.id ? 'bg-accent-d text-accent border-[rgba(0,217,163,0.2)]' : 'text-text2 border-transparent hover:bg-bg2'
                  }`}
                >
                  <input type="checkbox" checked={tp.status === 'confirmed'} onChange={() => confirmMutation.mutate(tp.id)} className="accent-accent" />
                  <span className="flex-1 truncate">{tp.title}</span>
                  <StatusPill variant={tp.priority === 'P0' ? 'red' : tp.priority === 'P1' ? 'amber' : 'gray'}>{tp.priority}</StatusPill>
                </div>
              ))}
            </div>
          ))}
          {testPoints.length === 0 && <div className="text-text3 text-[12px] text-center py-8">点击「AI 生成」创建测试点</div>}
        </div>

        {/* Center: Detail + streaming */}
        <div className="bg-bg1 border border-border rounded-[10px] p-4 overflow-y-auto">
          <ThinkingStream text={thinkingText} isStreaming={isStreaming && !contentText} />
          {contentText && (
            <div className="bg-bg2 rounded-lg p-4 border border-border mb-4 text-[12.5px] text-text leading-relaxed whitespace-pre-wrap">
              {contentText}
            </div>
          )}
          {selectedTP ? (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <StatusPill variant={selectedTP.priority === 'P0' ? 'red' : selectedTP.priority === 'P1' ? 'amber' : 'gray'}>{selectedTP.priority}</StatusPill>
                <StatusPill variant={selectedTP.source === 'ai' ? 'blue' : 'green'}>{selectedTP.source === 'ai' ? '🤖 AI' : '✏️ 手动'}</StatusPill>
                <StatusPill variant={selectedTP.status === 'confirmed' ? 'green' : 'gray'}>{selectedTP.status}</StatusPill>
              </div>
              <h2 className="text-[16px] font-semibold mb-2">{selectedTP.title}</h2>
              <div className="text-text2 text-[13px] leading-relaxed mb-4">{selectedTP.description ?? '暂无描述'}</div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-bg2 rounded-md p-3 border border-border">
                  <div className="text-[10px] text-text3 uppercase tracking-wide">分组</div>
                  <div className="text-[13px] font-medium mt-1">{selectedTP.group_name}</div>
                </div>
                <div className="bg-bg2 rounded-md p-3 border border-border">
                  <div className="text-[10px] text-text3 uppercase tracking-wide">预计用例数</div>
                  <div className="text-[13px] font-mono font-medium mt-1">{selectedTP.estimated_cases}</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-text3 text-[13px] text-center py-16">← 选择一个测试点查看详情</div>
          )}
        </div>

        {/* Right: Tree + stats */}
        <div className="bg-bg1 border border-border rounded-[10px] p-4 overflow-y-auto">
          <div className="text-[13px] font-semibold mb-3">场景树</div>
          <div className="mb-4">
            <div className="flex justify-between text-[11px] text-text3 mb-1">
              <span>确认进度</span>
              <span className="font-mono">{confirmedCount}/{testPoints.length}</span>
            </div>
            <ProgressBar value={testPoints.length ? (confirmedCount / testPoints.length) * 100 : 0} />
          </div>
          <div className="grid grid-cols-2 gap-2 mb-4">
            <div className="bg-bg2 rounded-md p-2.5 border border-border text-center">
              <div className="font-mono text-[18px] font-semibold text-accent">{testPoints.length}</div>
              <div className="text-[10px] text-text3">测试点</div>
            </div>
            <div className="bg-bg2 rounded-md p-2.5 border border-border text-center">
              <div className="font-mono text-[18px] font-semibold text-text">{totalEstimated}</div>
              <div className="text-[10px] text-text3">预计用例</div>
            </div>
          </div>
          {/* Tree visualization */}
          <div className="space-y-1">
            {allGroups.map((group) => (
              <div key={group} className="mb-2">
                <div className="text-[11px] font-semibold text-text2 mb-1">{groupIcons[group] ?? '📌'} {group}</div>
                {testPoints.filter((tp) => tp.group_name === group).map((tp, i, arr) => (
                  <div key={tp.id} className="flex items-center gap-1.5 ml-3 text-[11px]">
                    <span className="text-border2">{i === arr.length - 1 ? '└' : '├'}</span>
                    <span className={tp.status === 'confirmed' ? 'text-accent' : 'text-text3'}>{tp.title}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
