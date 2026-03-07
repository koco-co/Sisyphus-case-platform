import { Col, Row, Space, Typography } from 'antd'

import RegenerateCaseButton from '../components/RegenerateCaseButton'
import TestCaseDetailDrawer from '../components/TestCaseDetailDrawer'
import TestCaseTable from '../components/TestCaseTable'

const { Title, Paragraph } = Typography

export default function TestCaseWorkbenchPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>测试用例工作台</Title>
        <Paragraph>从测试点批量生成详细测试用例，并支持单条重生成与细节修订。</Paragraph>
      </div>
      <Space>
        <RegenerateCaseButton />
      </Space>
      <Row gutter={16}>
        <Col span={15}>
          <TestCaseTable />
        </Col>
        <Col span={9}>
          <TestCaseDetailDrawer />
        </Col>
      </Row>
    </div>
  )
}
