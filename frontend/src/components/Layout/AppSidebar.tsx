import { Menu, Button, Divider } from 'antd';
import {
  DashboardOutlined,
  FileSearchOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

import { useAppStore } from '../../stores/useAppStore';
import ProjectTree from './ProjectTree';

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '仪表盘',
  },
  {
    key: '/generate',
    icon: <ThunderboltOutlined />,
    label: '用例生成',
  },
  {
    key: '/testcases',
    icon: <FileSearchOutlined />,
    label: '测试用例',
  },
  {
    key: '/documents',
    icon: <FileTextOutlined />,
    label: '文档管理',
  },
];

export default function AppSidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarCollapsed } = useAppStore();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // Handle selected keys for routes with parameters
  const getSelectedKeys = () => {
    const path = location.pathname;
    // Match /generate or /generate/:projectId
    if (path.startsWith('/generate')) {
      return ['/generate'];
    }
    if (path.startsWith('/projects')) {
      return ['/projects'];
    }
    return [path];
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Logo */}
      {!sidebarCollapsed && (
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-gray-800">Sisyphus</h1>
          <p className="text-xs text-gray-500">测试用例生成平台</p>
        </div>
      )}

      {/* Project Tree */}
      {!sidebarCollapsed && (
        <div className="h-48 overflow-hidden border-b border-gray-100">
          <ProjectTree />
        </div>
      )}

      {/* Divider between project tree and menu */}
      {!sidebarCollapsed && <Divider style={{ margin: '8px 0' }} />}

      {/* Menu */}
      <div className="flex-1 overflow-auto">
        <Menu
          mode="inline"
          selectedKeys={getSelectedKeys()}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ height: '100%', borderRight: 0 }}
          inlineCollapsed={sidebarCollapsed}
        />
      </div>

      {/* Settings button */}
      <div className="p-4 border-t border-gray-200">
        <Button
          icon={<SettingOutlined />}
          block
          onClick={() => navigate('/settings')}
        >
          {!sidebarCollapsed && '设置'}
        </Button>
      </div>
    </div>
  );
}
