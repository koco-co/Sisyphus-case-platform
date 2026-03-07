import { Col, Row, Typography } from 'antd'

import CoverageMatrix from '../components/CoverageMatrix'
import PublishBar from '../components/PublishBar'
import RiskPanel from '../components/RiskPanel'

const { Title, Paragraph } = Typography

export default function ReviewDashboardPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>覆盖分析与发布</Title>
        <Paragraph>在发布前统一检查覆盖、风险和审核结论。</Paragraph>
      </div>
      <PublishBar />
      <Row gutter={16}>
        <Col span={14}>
          <CoverageMatrix />
        </Col>
        <Col span={10}>
          <RiskPanel />
        </Col>
      </Row>
    </div>
  )
}
