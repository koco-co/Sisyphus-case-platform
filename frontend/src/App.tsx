import { Layout } from 'antd';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppHeader from './components/Layout/AppHeader';
import AppSidebar from './components/Layout/AppSidebar';
import Dashboard from './pages/Dashboard';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';
import TestCaseList from './pages/TestCaseList';
import TestCaseDetail from './pages/TestCaseDetail';
import DocumentList from './pages/DocumentList';
import Settings from './pages/Settings';

const { Content } = Layout;

function App() {
  return (
    <BrowserRouter>
      <Layout style={{ minHeight: '100vh' }}>
        <AppSidebar />
        <Layout>
          <AppHeader />
          <Content style={{ margin: '16px' }}>
            <div style={{ padding: 24, minHeight: 360, background: '#fff', borderRadius: 8 }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/projects" element={<ProjectList />} />
                <Route path="/projects/:id" element={<ProjectDetail />} />
                <Route path="/testcases" element={<TestCaseList />} />
                <Route path="/testcases/:id" element={<TestCaseDetail />} />
                <Route path="/documents" element={<DocumentList />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </Content>
        </Layout>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
