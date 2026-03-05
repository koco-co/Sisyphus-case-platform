import { Card, Typography, Tag, Spin, Alert, Progress } from 'antd';
import { FileTextOutlined, FilePdfOutlined, FileMarkdownOutlined, CloseOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';

const { Text } = Typography;

interface FilePreviewProps {
  filename: string;
  mimeType?: string;
  size?: number;
  content?: string;
  loading?: boolean;
  progress?: number;
  error?: string;
  onRemove?: () => void;
}

function getFileIcon(mimeType?: string) {
  if (!mimeType) return <FileTextOutlined />;
  if (mimeType.includes('pdf')) return <FilePdfOutlined className="text-red-500" />;
  if (mimeType.includes('markdown') || mimeType.includes('md')) return <FileMarkdownOutlined className="text-blue-500" />;
  return <FileTextOutlined className="text-gray-500" />;
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileTypeTag(mimeType?: string): string {
  if (!mimeType) return '未知';
  if (mimeType.includes('pdf')) return 'PDF';
  if (mimeType.includes('markdown')) return 'Markdown';
  if (mimeType.includes('text')) return '文本';
  return '文档';
}

export default function FilePreview({
  filename,
  mimeType,
  size,
  content,
  loading,
  progress,
  error,
  onRemove,
}: FilePreviewProps) {
  return (
    <Card
      className="mb-4"
      size="small"
      title={
        <div className="flex items-center gap-2">
          {getFileIcon(mimeType)}
          <span className="font-medium">{filename}</span>
          {size && (
            <Tag color="default" className="ml-2">
              {formatFileSize(size)}
            </Tag>
          )}
          <Tag color="blue">{getFileTypeTag(mimeType)}</Tag>
        </div>
      }
      extra={
        onRemove && (
          <button
            onClick={onRemove}
            className="text-gray-400 hover:text-red-500 transition-colors"
          >
            <CloseOutlined />
          </button>
        )
      }
    >
      {loading && (
        <div className="py-8 text-center">
          <Spin />
          <div className="mt-3">
            <Progress percent={progress} size="small" />
          </div>
          <Text type="secondary" className="block mt-2">
            正在解析文档...
          </Text>
        </div>
      )}

      {error && (
        <Alert
          type="error"
          message="解析失败"
          description={error}
          showIcon
        />
      )}

      {!loading && !error && content && (
        <div className="max-h-96 overflow-y-auto">
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
      )}

      {!loading && !error && !content && (
        <Text type="secondary">等待解析...</Text>
      )}
    </Card>
  );
}
