import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import RequirementIntakePage from './modules/intake/pages/RequirementIntakePage';
import RequirementStructurePage from './modules/requirement/pages/RequirementStructurePage';
import TestPointPage from './modules/test-points/pages/TestPointPage';
import TestCaseWorkbenchPage from './modules/test-cases/pages/TestCaseWorkbenchPage';
import ReviewDashboardPage from './modules/review/pages/ReviewDashboardPage';
import KnowledgeLibraryPage from './modules/knowledge/pages/KnowledgeLibraryPage';
import IntegrationSettingsPage from './modules/integrations/pages/IntegrationSettingsPage';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="intake" element={<RequirementIntakePage />} />
            <Route path="structure" element={<RequirementStructurePage />} />
            <Route path="test-points" element={<TestPointPage />} />
            <Route path="cases" element={<TestCaseWorkbenchPage />} />
            <Route path="review" element={<ReviewDashboardPage />} />
            <Route path="knowledge" element={<KnowledgeLibraryPage />} />
            <Route path="integrations" element={<IntegrationSettingsPage />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
