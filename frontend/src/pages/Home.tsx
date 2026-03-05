import { message } from 'antd';

import ChatInput from '../components/Chat/ChatInput';
import type { UploadedFile } from '../components/Chat/ChatInput';

export default function Home() {
  const handleSend = (msg: string, files: UploadedFile[]) => {
    console.log('Send:', msg, files);
    // TODO: Implement WebSocket connection
    message.info('发送功能待实现');
  };

  const handleFileUpload = (file: UploadedFile) => {
    console.log('File uploaded:', file);
    // TODO: Implement file upload API
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat area */}
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-2xl px-4">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            测试用例生成平台
          </h1>
          <p className="text-gray-500 mb-8">
            上传需求文档，自动生成功能测试用例
          </p>
          <div className="text-gray-400 text-sm">
            支持 Markdown、纯文本、PDF 格式的需求文档
          </div>
        </div>
      </div>

      {/* Input area */}
      <div className="p-4 bg-transparent">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSend={handleSend}
            onFileUpload={handleFileUpload}
          />
        </div>
      </div>
    </div>
  );
}
