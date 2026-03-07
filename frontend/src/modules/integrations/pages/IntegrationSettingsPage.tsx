import { Button, Space, Typography } from 'antd'

import FieldMappingEditor from '../components/FieldMappingEditor'

const { Title, Paragraph } = Typography

export default function IntegrationSettingsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>集成与导出</Title>
        <Paragraph>配置外部系统连接、字段映射，并执行标准化导出。</Paragraph>
      </div>
      <Space>
        <Button type="primary">执行 Markdown 导出</Button>
      </Space>
      <FieldMappingEditor />
    </div>
  )
}
