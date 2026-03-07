import { Card, Descriptions, Tag, Typography } from 'antd'

const { Paragraph } = Typography

interface PreprocessStatusCardProps {
  status: string
  currentStage: string
  summary?: string | null
}

export default function PreprocessStatusCard({ status, currentStage, summary }: PreprocessStatusCardProps) {
  return (
    <Card title="预处理状态">
      <Descriptions column={1} size="small">
        <Descriptions.Item label="任务状态">
          <Tag color="blue">{status}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="当前阶段">{currentStage}</Descriptions.Item>
      </Descriptions>
      {summary ? <Paragraph className="mb-0">{summary}</Paragraph> : null}
    </Card>
  )
}
