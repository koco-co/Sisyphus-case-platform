import { InboxOutlined } from '@ant-design/icons'
import { Upload, Typography } from 'antd'
import type { UploadProps } from 'antd'

const { Dragger } = Upload
const { Paragraph } = Typography

interface UploadPanelProps {
  onSelectFile?: (file: File) => void
}

export default function UploadPanel({ onSelectFile }: UploadPanelProps) {
  const uploadProps: UploadProps = {
    multiple: false,
    beforeUpload: (file) => {
      onSelectFile?.(file)
      return false
    },
    showUploadList: true,
  }

  return (
    <div>
      <Dragger {...uploadProps} data-testid="intake-uploader">
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽上传需求文档</p>
        <Paragraph type="secondary">
          支持 Word、PDF、Markdown、图片以及后续 OCR / 口述转写接入
        </Paragraph>
      </Dragger>
    </div>
  )
}
