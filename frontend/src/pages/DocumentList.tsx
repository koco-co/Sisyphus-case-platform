import { Typography, Table, Button, Space, Upload } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Title } = Typography;

const columns = [
  {
    title: '文档名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
  },
  {
    title: '上传时间',
    dataIndex: 'uploadedAt',
    key: 'uploadedAt',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
  },
  {
    title: '操作',
    key: 'action',
    render: () => (
      <Space>
        <Button type="link">查看</Button>
        <Button type="link" danger>
          删除
        </Button>
      </Space>
    ),
  },
];

const uploadProps: UploadProps = {
  name: 'file',
  multiple: true,
  showUploadList: false,
  beforeUpload: () => {
    return false;
  },
};

export default function DocumentList() {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>文档管理</Title>
        <Upload {...uploadProps}>
          <Button type="primary" icon={<UploadOutlined />}>
            上传文档
          </Button>
        </Upload>
      </div>
      <Table columns={columns} dataSource={[]} rowKey="id" />
    </div>
  );
}
