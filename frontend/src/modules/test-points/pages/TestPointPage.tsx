import { Col, Row, Space, Typography } from 'antd'

import AiGapCheckButton from '../components/AiGapCheckButton'
import TestPointDetailPanel from '../components/TestPointDetailPanel'
import TestPointTree from '../components/TestPointTree'

const { Title, Paragraph } = Typography

export default function TestPointPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>测试点设计</Title>
        <Paragraph>基于结构化需求生成并校验测试点树。</Paragraph>
      </div>
      <Space>
        <AiGapCheckButton />
      </Space>
      <Row gutter={16}>
        <Col span={10}>
          <TestPointTree />
        </Col>
        <Col span={14}>
          <TestPointDetailPanel />
        </Col>
      </Row>
    </div>
  )
}
