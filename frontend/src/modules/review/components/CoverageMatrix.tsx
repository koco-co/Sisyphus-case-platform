import { Card, Descriptions } from 'antd'

export default function CoverageMatrix() {
  return (
    <Card title="覆盖矩阵">
      <Descriptions column={1} size="small">
        <Descriptions.Item label="需求模块">1</Descriptions.Item>
        <Descriptions.Item label="测试点">1</Descriptions.Item>
        <Descriptions.Item label="详细用例">1</Descriptions.Item>
      </Descriptions>
    </Card>
  )
}
