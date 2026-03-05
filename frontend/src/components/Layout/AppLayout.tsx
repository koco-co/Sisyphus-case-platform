import { Outlet } from 'react-router-dom';
import { Layout } from 'antd';

import AppSidebar from './AppSidebar';
import { useAppStore } from '../../stores/useAppStore';

const { Content, Sider } = Layout;

export default function AppLayout() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <Layout className="h-screen">
      <Sider
        collapsible
        collapsed={sidebarCollapsed}
        onCollapse={toggleSidebar}
        width={280}
        className="bg-white border-r border-gray-200"
      >
        <AppSidebar />
      </Sider>
      <Content className="overflow-auto bg-gray-50">
        <Outlet />
      </Content>
    </Layout>
  );
}
