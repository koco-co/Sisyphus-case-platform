import { Card, Typography } from 'antd'

const { Paragraph } = Typography

export default function FieldMappingEditor() {
  return (
    <Card title="字段映射">
      <Paragraph className="mb-0">本页用于维护平台字段与外部系统字段之间的映射关系。</Paragraph>
    </Card>
  )
}
