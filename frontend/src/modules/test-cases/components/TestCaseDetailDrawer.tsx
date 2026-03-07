import { Card, Descriptions } from 'antd'

export default function TestCaseDetailDrawer() {
  return (
    <Card title="用例详情">
      <Descriptions column={1} size="small">
        <Descriptions.Item label="前置条件">已完成基础主数据准备</Descriptions.Item>
        <Descriptions.Item label="预期结果">处理完成后状态明确可追踪</Descriptions.Item>
      </Descriptions>
    </Card>
  )
}
