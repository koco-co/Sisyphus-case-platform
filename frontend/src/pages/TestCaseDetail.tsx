import { useParams } from 'react-router-dom';
import { Spin, Empty, Result } from 'antd';

import { useTestCase } from '../hooks/useTestCases';
import TestCaseDetailComponent from '../components/TestCase/TestCaseDetail';

export default function TestCaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: testCase, isLoading, error } = useTestCase(id!);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <Result
          status="error"
          title="加载失败"
          subTitle="无法获取用例详情，请稍后重试"
        />
      </div>
    );
  }

  if (!testCase) {
    return (
      <div className="flex items-center justify-center h-full">
        <Empty description="用例不存在" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <TestCaseDetailComponent testCase={testCase} />
      </div>
    </div>
  );
}
