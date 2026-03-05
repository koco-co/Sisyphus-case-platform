import { Card, Table, Tag, Descriptions, Button } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';

import type { TestCase } from '../../hooks/useTestCases';

interface TestCaseDetailProps {
  testCase: TestCase;
}

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

export default function TestCaseDetail({ testCase }: TestCaseDetailProps) {
  const columns = [
    {
      title: '序号',
      dataIndex: 'step',
      key: 'step',
      width: 80,
      align: 'center' as const,
    },
    {
      title: '操作步骤',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '预期结果',
      dataIndex: 'expected',
      key: 'expected',
    },
  ];

  return (
    <div>
      {/* 返回导航 */}
      <div className="flex items-center gap-4 mb-6">
        <Link to={`/requirements/${testCase.requirementId}`}>
          <Button type="text" icon={<ArrowLeftOutlined />}>
            返回用例列表
          </Button>
        </Link>
        <span className="text-gray-300">|</span>
        <Link
          to={`/requirements/${testCase.requirementId}`}
          className="text-blue-600 hover:underline text-sm"
        >
          查看需求详情
        </Link>
      </div>

      {/* 用例信息 */}
      <Card>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="用例标题" span={2}>
            <span className="font-medium">{testCase.title}</span>
          </Descriptions.Item>
          <Descriptions.Item label="优先级">
            <Tag color={priorityColors[testCase.priority]}>
              {priorityLabels[testCase.priority] || testCase.priority}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="标签">
            {testCase.tags?.length > 0 ? (
              testCase.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)
            ) : (
              <span className="text-gray-400">无</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="前置条件" span={2}>
            {testCase.preconditions || <span className="text-gray-400">无</span>}
          </Descriptions.Item>
        </Descriptions>

        {/* 测试步骤 */}
        <h4 className="font-bold mt-6 mb-4 text-base">测试步骤</h4>
        <Table
          columns={columns}
          dataSource={testCase.steps || []}
          rowKey="step"
          pagination={false}
          bordered
          size="small"
        />
      </Card>
    </div>
  );
}
