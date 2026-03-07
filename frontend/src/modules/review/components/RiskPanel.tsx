import { Card, Typography } from 'antd'

const { Paragraph } = Typography

export default function RiskPanel() {
  return (
    <Card title="风险与缺口">
      <Paragraph className="mb-0">当前演示数据已覆盖主流程，仍需补充边界与异常流。</Paragraph>
    </Card>
  )
}
