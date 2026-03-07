import { Card, Descriptions } from 'antd'

export default function TestPointDetailPanel() {
  return (
    <Card title="测试点详情">
      <Descriptions column={1} size="small">
        <Descriptions.Item label="类型">main_flow</Descriptions.Item>
        <Descriptions.Item label="模块">Settlement</Descriptions.Item>
      </Descriptions>
    </Card>
  )
}
