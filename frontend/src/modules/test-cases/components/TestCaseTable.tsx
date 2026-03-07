import { Card, Table } from 'antd'

const dataSource = [
  {
    key: '1',
    module: 'Settlement',
    title: 'Settlement - 主流程校验',
    priority: 'P1',
  },
]

export default function TestCaseTable() {
  return (
    <Card title="测试用例列表">
      <Table
        pagination={false}
        dataSource={dataSource}
        columns={[
          { title: '模块', dataIndex: 'module' },
          { title: '标题', dataIndex: 'title' },
          { title: '优先级', dataIndex: 'priority' },
        ]}
      />
    </Card>
  )
}
