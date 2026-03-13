'use client';

import { CheckCircle, Loader2, PlusCircle, Send, SkipForward } from 'lucide-react';
import { useCallback, useRef, useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  disabled?: boolean;
}

const quickActions = [
  { label: '跳过', icon: SkipForward, message: '跳过当前问题' },
  { label: '已知晓', icon: CheckCircle, message: '已知晓，继续下一步' },
  { label: '需要补充', icon: PlusCircle, message: '我需要补充以下信息：' },
];

export function ChatInput({ onSend, isStreaming, disabled }: ChatInputProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    if (!text.trim() || isStreaming || disabled) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [text, isStreaming, disabled, onSend]);

  const handleQuickAction = useCallback(
    (message: string) => {
      if (isStreaming || disabled) return;
      // If message ends with colon, fill input instead of sending
      if (message.endsWith('：')) {
        setText(message);
        textareaRef.current?.focus();
        return;
      }
      onSend(message);
    },
    [isStreaming, disabled, onSend],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, []);

  return (
    <div className="border-t border-border bg-bg1 p-3 flex-shrink-0">
      {/* Quick Actions */}
      <div className="flex gap-1.5 mb-2">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              type="button"
              onClick={() => handleQuickAction(action.message)}
              disabled={isStreaming || disabled}
              className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-bg2 border border-border text-text3 hover:text-text2 hover:border-border2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Icon className="w-3 h-3" />
              {action.label}
            </button>
          );
        })}
      </div>

      {/* Input Area */}
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="输入分析问题，如：请对这个需求进行需求分析..."
          disabled={isStreaming || disabled}
          rows={1}
          className="flex-1 resize-none bg-bg2 border border-border rounded-lg px-3 py-2 text-[13px] text-text placeholder:text-text3 outline-none focus:border-accent transition-colors disabled:opacity-50"
          style={{ minHeight: '40px', maxHeight: '120px' }}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={isStreaming || disabled || !text.trim()}
          className="flex-shrink-0 inline-flex items-center justify-center w-9 h-9 rounded-lg bg-accent text-white dark:text-black font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent2 transition-colors"
        >
          {isStreaming ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );
}
