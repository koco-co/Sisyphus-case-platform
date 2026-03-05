import { useState, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';

import FileUploadButton from './FileUploadButton';

const { TextArea } = Input;

export interface UploadedFile {
  uid: string;
  name: string;
  size: number;
  file: File;
}

interface ChatInputProps {
  onSend: (message: string, files: UploadedFile[]) => void;
  onFileUpload: (file: UploadedFile) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  onFileUpload,
  disabled,
  placeholder = '描述你想要生成的测试用例...',
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!message.trim() && files.length === 0) return;

    onSend(message, files);
    setMessage('');
    setFiles([]);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = (file: File) => {
    const uploadedFile: UploadedFile = {
      uid: `${Date.now()}-${file.name}`,
      name: file.name,
      size: file.size,
      file,
    };
    setFiles((prev) => [...prev, uploadedFile]);
    onFileUpload(uploadedFile);
  };

  const handleRemoveFile = (uid: string) => {
    setFiles((prev) => prev.filter((f) => f.uid !== uid));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      {/* 已上传文件列表 */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 p-3 border-b border-gray-100">
          {files.map((file) => (
            <div
              key={file.uid}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-600 rounded-full text-sm"
            >
              <span className="max-w-[150px] truncate">{file.name}</span>
              <span className="text-blue-400 text-xs">
                ({formatFileSize(file.size)})
              </span>
              <button
                onClick={() => handleRemoveFile(file.uid)}
                className="text-blue-400 hover:text-blue-600 ml-1"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 输入区域 */}
      <div className="flex items-end p-3 gap-2">
        <FileUploadButton onUpload={handleFileUpload} disabled={disabled} />

        <TextArea
          ref={textAreaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoSize={{ minRows: 1, maxRows: 4 }}
          className="flex-1 border-none shadow-none resize-none focus:ring-0 text-base"
          styles={{
            textarea: {
              padding: '8px 0',
            },
          }}
        />

        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={disabled || (!message.trim() && files.length === 0)}
          className="flex-shrink-0"
        />
      </div>

      {/* 提示文字 */}
      <div className="px-3 pb-2 text-xs text-gray-400">
        按 Enter 发送，Shift + Enter 换行
      </div>
    </div>
  );
}
