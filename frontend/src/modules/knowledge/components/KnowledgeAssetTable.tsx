import { Card, Typography } from 'antd'

const { Paragraph, Text } = Typography

const dataSource = [
  {
    key: '1',
    title: 'Settlement package',
    status: 'candidate',
  },
]

export default function KnowledgeAssetTable() {
  return (
    <Card title="知识资产列表">
      <div className="space-y-3">
        {dataSource.map((item) => (
          <div key={item.key} className="rounded border border-slate-200 p-3">
            <Text strong>{item.title}</Text>
            <Paragraph className="mb-0 mt-2">状态：{item.status}</Paragraph>
          </div>
        ))}
      </div>
    </Card>
  )
}
