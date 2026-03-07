import { Typography, Card, Row, Col, Statistic } from 'antd';
import {
  ProjectOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';

const { Title } = Typography;

export default function Dashboard() {
  return (
    <div>
      <Title level={2}>仪表盘</Title>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="项目总数"
              value={0}
              prefix={<ProjectOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="文档总数"
              value={0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已生成用例"
              value={0}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待审核"
              value={0}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
