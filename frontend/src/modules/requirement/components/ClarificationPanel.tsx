import { Card, Typography } from 'antd'

const { Paragraph } = Typography

const clarificationItems = [
  '是否存在跨系统回写场景？',
  '结算周期边界是否需要单独测试？',
]

export default function ClarificationPanel() {
  return (
    <Card title="待确认问题">
      <div className="space-y-2">
        {clarificationItems.map((item) => (
          <Paragraph key={item} className="mb-0 rounded bg-slate-50 px-3 py-2">
            {item}
          </Paragraph>
        ))}
      </div>
    </Card>
  )
}
