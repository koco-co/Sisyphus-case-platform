import { Col, Row, Typography } from 'antd'

import ClarificationPanel from '../components/ClarificationPanel'
import SourcePane from '../components/SourcePane'
import StructureEditor from '../components/StructureEditor'

const { Title, Paragraph } = Typography

export default function RequirementStructurePage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>需求结构化</Title>
        <Paragraph>在进入测试点设计前，先对需求进行结构化抽取、确认和补充。</Paragraph>
      </div>
      <Row gutter={16}>
        <Col span={8}>
          <SourcePane />
        </Col>
        <Col span={10}>
          <StructureEditor />
        </Col>
        <Col span={6}>
          <ClarificationPanel />
        </Col>
      </Row>
    </div>
  )
}
