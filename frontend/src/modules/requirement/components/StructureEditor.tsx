import { Card, Tag, Typography } from 'antd'

const { Paragraph, Text } = Typography

const demoModules = [
  { name: 'Settlement', summary: 'Validate account period and posting rules.' },
]

export default function StructureEditor() {
  return (
    <Card title="结构化结果">
      <div className="space-y-3">
        {demoModules.map((item) => (
          <div key={item.name} className="rounded border border-slate-200 p-3">
            <div className="flex items-center justify-between">
              <Text strong>{item.name}</Text>
              <Tag color="blue">draft</Tag>
            </div>
            <Paragraph className="mb-0 mt-2">{item.summary}</Paragraph>
          </div>
        ))}
      </div>
    </Card>
  )
}
