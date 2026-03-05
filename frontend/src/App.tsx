import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

import AppLayout from './components/Layout/AppLayout';
import Home from './pages/Home';
import Requirement from './pages/Requirement';
import TestCaseDetail from './pages/TestCaseDetail';
import Settings from './pages/Settings';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          {/* Main layout with collapsible sidebar */}
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Home />} />
            <Route path="projects/:projectId" element={<Home />} />
            <Route path="requirements/:id" element={<Requirement />} />
            <Route path="testcases/:id" element={<TestCaseDetail />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
