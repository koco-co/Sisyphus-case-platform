'use client';

import { CheckCircle, Loader2, Plug, XCircle } from 'lucide-react';
import { useState } from 'react';

interface ConnectionTestButtonProps {
  testUrl: string;
  label?: string;
  className?: string;
}

type TestStatus = 'idle' | 'testing' | 'ok' | 'error';

export function ConnectionTestButton({
  testUrl,
  label = '测试连接',
  className = '',
}: ConnectionTestButtonProps) {
  const [status, setStatus] = useState<TestStatus>('idle');
  const [message, setMessage] = useState('');

  const handleTest = async () => {
    setStatus('testing');
    setMessage('');

    try {
      const res = await fetch(testUrl, { method: 'POST' });
      const data = await res.json();

      if (data.status === 'ok') {
        setStatus('ok');
        setMessage(data.response_preview || '连接成功');
      } else {
        setStatus('error');
        setMessage(data.error || '连接失败');
      }
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : '网络错误');
    }

    setTimeout(() => {
      setStatus('idle');
      setMessage('');
    }, 5000);
  };

  const iconMap = {
    idle: <Plug className="w-3.5 h-3.5" />,
    testing: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    ok: <CheckCircle className="w-3.5 h-3.5 text-sy-accent" />,
    error: <XCircle className="w-3.5 h-3.5 text-sy-danger" />,
  };

  const labelMap = {
    idle: label,
    testing: '测试中...',
    ok: '连接成功',
    error: '连接失败',
  };

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <button
        type="button"
        className="btn btn-sm btn-outline flex items-center gap-1.5"
        onClick={() => void handleTest()}
        disabled={status === 'testing'}
      >
        {iconMap[status]}
        <span className="text-[12px]">{labelMap[status]}</span>
      </button>
      {message && (
        <p
          className={`text-[11px] truncate max-w-[240px] ${status === 'ok' ? 'text-sy-accent' : 'text-sy-danger'}`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
