import { Typography, Card } from 'antd';
import LLMConfig from '../components/Settings/LLMConfig';

const { Title } = Typography;

export default function Settings() {
  return (
    <div className="h-full overflow-auto p-6 bg-gray-50">
      <div className="max-w-2xl mx-auto">
        <Title level={3}>设置</Title>

        <Card title="LLM 配置" className="mt-4">
          <LLMConfig />
        </Card>
      </div>
    </div>
  );
}
