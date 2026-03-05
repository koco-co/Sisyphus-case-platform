import { useParams, Link } from 'react-router-dom';
import { Button, Card, List, Row, Col, Spin, Empty, Tag, Typography, Space } from 'antd';
import { ArrowLeftOutlined, FileTextOutlined } from '@ant-design/icons';

import { useRequirement, useTestCases } from '../hooks';
import RequirementDetail from '../components/Requirement/RequirementDetail';

const { Text } = Typography;

const priorityColors: Record<string, string> = {
  P0: 'red',
  P1: 'orange',
  P2: 'blue',
  P3: 'gray',
};

const priorityLabels: Record<string, string> = {
  P0: '紧急',
  P1: '高',
  P2: '中',
  P3: '低',
};

export default function Requirement() {
  const { id } = useParams<{ id: string }>();
  const { data: requirement, isLoading: requirementLoading, error: requirementError } = useRequirement(id || '');
  const { data: testCases, isLoading: testCasesLoading } = useTestCases(id || '');

  if (requirementError) {
    return (
      <div className="p-6">
        <Empty
          description="加载需求失败"
          className="py-20"
        >
          <Link to="/">
            <Button type="primary">返回首页</Button>
          </Link>
        </Empty>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 返回按钮 */}
      <div className="mb-6">
        <Link to="/">
          <Button type="text" icon={<ArrowLeftOutlined />}>
            返回项目列表
          </Button>
        </Link>
      </div>

      <Row gutter={24}>
        {/* 左侧: 需求详情 */}
        <Col xs={24} lg={16}>
          <RequirementDetail
            requirement={requirement}
            loading={requirementLoading}
          />
        </Col>

        {/* 右侧: 关联的测试用例 */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <Space>
                <FileTextOutlined />
                <span>关联测试用例</span>
                {testCases && (
                  <Tag color="blue">{testCases.length}</Tag>
                )}
              </Space>
            }
            className="sticky top-6"
          >
            {testCasesLoading ? (
              <div className="flex justify-center py-10">
                <Spin />
              </div>
            ) : testCases && testCases.length > 0 ? (
              <List
                dataSource={testCases}
                renderItem={(testCase) => (
                  <List.Item className="cursor-pointer hover:bg-gray-50 rounded px-2">
                    <Link
                      to={`/testcases/${testCase.id}`}
                      className="w-full"
                    >
                      <div className="flex items-center justify-between">
                        <Text className="flex-1 truncate" ellipsis>
                          {testCase.title}
                        </Text>
                        <Tag color={priorityColors[testCase.priority]}>
                          {priorityLabels[testCase.priority] || testCase.priority}
                        </Tag>
                      </div>
                    </Link>
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                description="暂无关联的测试用例"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
