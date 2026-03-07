import { Card, Typography } from 'antd'

const { Paragraph } = Typography

export default function SourcePane() {
  return (
    <Card title="原始需求">
      <Paragraph type="secondary">展示 OCR、转写或文档原文，供结构化校对使用。</Paragraph>
    </Card>
  )
}
