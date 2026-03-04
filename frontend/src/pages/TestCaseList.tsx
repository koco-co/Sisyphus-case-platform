import { Typography, Table, Button, Space, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const { Title } = Typography;

const columns = [
  {
    title: '用例标题',
    dataIndex: 'title',
    key: 'title',
  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    render: (priority: string) => {
      const color = priority === 'P0' ? 'red' : priority === 'P1' ? 'orange' : 'blue';
      return <Tag color={color}>{priority}</Tag>;
    },
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => {
      const color = status === 'approved' ? 'green' : status === 'pending' ? 'orange' : 'default';
      const text = status === 'approved' ? '已审核' : status === 'pending' ? '待审核' : status;
      return <Tag color={color}>{text}</Tag>;
    },
  },
  {
    title: '所属项目',
    dataIndex: 'projectName',
    key: 'projectName',
  },
  {
    title: '操作',
    key: 'action',
    render: () => (
      <Space>
        <Button type="link">查看</Button>
        <Button type="link">审核</Button>
      </Space>
    ),
  },
];

export default function TestCaseList() {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>测试用例</Title>
        <Button type="primary" icon={<PlusOutlined />}>
          生成用例
        </Button>
      </div>
      <Table columns={columns} dataSource={[]} rowKey="id" />
    </div>
  );
}
