import { Layout, Typography, Space } from 'antd';
import { GithubOutlined, SettingOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Header } = Layout;
const { Text } = Typography;

export default function AppHeader() {
  const navigate = useNavigate();

  return (
    <Header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#fff',
        padding: '0 24px',
        borderBottom: '1px solid #f0f0f0',
      }}
    >
      <Space>
        <GithubOutlined style={{ fontSize: 24, color: '#1677ff' }} />
        <Text strong style={{ fontSize: 18 }}>
          Sisyphus 测试用例生成平台
        </Text>
      </Space>
      <Space>
        <SettingOutlined
          style={{ fontSize: 18, cursor: 'pointer' }}
          onClick={() => navigate('/settings')}
        />
      </Space>
    </Header>
  );
}
