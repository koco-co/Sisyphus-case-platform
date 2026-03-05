import { Upload, Button, message } from 'antd';
import { PaperClipOutlined } from '@ant-design/icons';

interface FileUploadButtonProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export default function FileUploadButton({ onUpload, disabled }: FileUploadButtonProps) {
  return (
    <Upload
      accept=".md,.txt,.pdf"
      showUploadList={false}
      beforeUpload={(file) => {
        // 检查文件大小 (10MB)
        if (file.size > 10 * 1024 * 1024) {
          message.error('文件大小不能超过 10MB');
          return false;
        }

        onUpload(file);
        return false; // 阻止自动上传
      }}
      disabled={disabled}
    >
      <Button
        type="text"
        icon={<PaperClipOutlined className="text-xl" />}
        className="text-gray-400 hover:text-gray-600"
      />
    </Upload>
  );
}
