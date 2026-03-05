import { Card, Progress, Tag, Typography, Empty } from 'antd';
import { CheckCircleOutlined, LoadingOutlined, CloseCircleOutlined } from '@ant-design/icons';
import type { GenerationProgress, TestCase } from '../../hooks/useGeneration';

const { Text, Paragraph } = Typography;

const stageConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  idle: { color: 'default', icon: null, label: '等待中' },
  connecting: { color: 'processing', icon: <LoadingOutlined />, label: '连接中' },
  retrieving: { color: 'processing', icon: <LoadingOutlined />, label: '检索历史用例' },
  generating: { color: 'processing', icon: <LoadingOutlined />, label: '生成用例' },
  reviewing: { color: 'processing', icon: <LoadingOutlined />, label: '审核用例' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, label: '完成' },
  error: { color: 'error', icon: <CloseCircleOutlined />, label: '错误' },
};

function TestCaseCard({ testCase, index }: { testCase: TestCase; index: number }) {
  return (
    <Card
      className="mb-3"
      size="small"
      title={
        <div className="flex items-center gap-2">
          <span className="text-gray-500">#{index + 1}</span>
          <span>{testCase.title}</span>
          <Tag color={testCase.priority === 'P0' ? 'red' : testCase.priority === 'P1' ? 'orange' : 'blue'}>
            {testCase.priority}
          </Tag>
        </div>
      }
    >
      {testCase.preconditions && (
        <div className="mb-2">
          <Text type="secondary" className="text-xs">前置条件：</Text>
          <Paragraph className="mb-0 text-sm">{testCase.preconditions}</Paragraph>
        </div>
      )}
      {testCase.steps && testCase.steps.length > 0 && (
        <div>
          <Text type="secondary" className="text-xs">测试步骤：</Text>
          <div className="mt-1">
            {testCase.steps.map((step, i) => (
              <div key={i} className="flex gap-2 text-sm mb-1">
                <span className="text-gray-400">{step.step}.</span>
                <span>{step.action}</span>
                <span className="text-gray-400">→</span>
                <span className="text-green-600">{step.expected}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

export default function StreamingMessage({ progress, testCases }: { progress: GenerationProgress; testCases?: TestCase[] }) {
  const config = stageConfig[progress.stage] || stageConfig.idle;
  const showProgress = ['connecting', 'retrieving', 'generating', 'reviewing'].includes(progress.stage);

  if (progress.stage === 'idle' && !testCases?.length) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      {/* 进度显示 */}
      <div className="flex items-center gap-3 mb-4">
        <Tag color={config.color} icon={config.icon}>
          {config.label}
        </Tag>
        <Text>{progress.message}</Text>
      </div>

      {/* 进度条 */}
      {showProgress && (
        <Progress
          percent={progress.progress}
          status={progress.stage === 'error' ? 'exception' : 'active'}
          size="small"
          className="mb-4"
        />
      )}

      {/* 生成的用例 */}
      {progress.stage === 'completed' && testCases && testCases.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircleOutlined className="text-green-500" />
            <Text strong>生成了 {testCases.length} 个测试用例</Text>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {testCases.map((tc, i) => (
              <TestCaseCard key={tc.id || i} testCase={tc} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* 错误显示 */}
      {progress.stage === 'error' && (
        <div className="text-red-500">
          <CloseCircleOutlined className="mr-2" />
          {progress.message}
        </div>
      )}

      {/* 空结果 */}
      {progress.stage === 'completed' && (!testCases || testCases.length === 0) && (
        <Empty description="未生成任何测试用例" />
      )}
    </div>
  );
}
