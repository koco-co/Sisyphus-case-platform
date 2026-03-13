'use client';

import { Loader2, X } from 'lucide-react';
import { type ReactNode, useEffect, useRef } from 'react';

interface FormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: () => void;
  title: string;
  children: ReactNode;
  submitText?: string;
  cancelText?: string;
  loading?: boolean;
  width?: number;
}

export function FormDialog({
  open,
  onClose,
  onSubmit,
  title,
  children,
  submitText = '确认',
  cancelText = '取消',
  loading = false,
  width = 440,
}: FormDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    else if (!open && el.open) el.close();
  }, [open]);

  if (!open) return null;

  return (
    <dialog
      ref={dialogRef}
      className="fixed inset-0 z-50 m-auto rounded-lg border border-border bg-bg1 p-0 shadow-lg backdrop:bg-black/50"
      style={{ width }}
      onClose={onClose}
    >
      <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-border">
        <h3 className="text-[14px] font-semibold text-text">{title}</h3>
        <button
          type="button"
          onClick={onClose}
          className="text-text3 hover:text-text transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="px-5 py-4">{children}</div>

      <div className="flex justify-end gap-2 px-5 pb-4">
        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="px-3 py-1.5 rounded-md text-[12.5px] font-medium border border-border bg-bg2 text-text2 hover:bg-bg3 transition-colors disabled:opacity-50"
        >
          {cancelText}
        </button>
        <button
          type="button"
          onClick={onSubmit}
          disabled={loading}
          className="px-3 py-1.5 rounded-md text-[12.5px] font-medium bg-accent text-white hover:bg-accent2 transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
        >
          {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          {submitText}
        </button>
      </div>
    </dialog>
  );
}
