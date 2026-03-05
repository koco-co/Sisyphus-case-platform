import { Card, Descriptions, Tag, Typography, Empty } from 'antd';
import type { Module, Feature } from '../../hooks/useRequirement';

const { Text, Paragraph } = Typography;

interface ModuleCardProps {
  module: Module;
  moduleIndex: number;
}

function FeatureItem({ feature, index }: { feature: Feature; index: number }) {
  return (
    <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
      <div className="flex items-center gap-2 mb-2">
        <Tag color="blue">{index + 1}</Tag>
        <Text strong className="text-base">{feature.name}</Text>
      </div>
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="功能描述">
          <Paragraph className="mb-0">{feature.description || '暂无描述'}</Paragraph>
        </Descriptions.Item>
        <Descriptions.Item label="输入">
          <Paragraph className="mb-0" type="secondary">
            {feature.input || '无'}
          </Paragraph>
        </Descriptions.Item>
        <Descriptions.Item label="输出">
          <Paragraph className="mb-0" type="success">
            {feature.output || '无'}
          </Paragraph>
        </Descriptions.Item>
        <Descriptions.Item label="异常处理">
          <Paragraph className="mb-0" type="warning">
            {feature.exceptions || '无'}
          </Paragraph>
        </Descriptions.Item>
      </Descriptions>
    </div>
  );
}

export default function ModuleCard({ module, moduleIndex }: ModuleCardProps) {
  return (
    <Card
      className="mb-4"
      title={
        <div className="flex items-center gap-2">
          <Tag color="purple">模块 {moduleIndex + 1}</Tag>
          <span className="font-bold text-lg">{module.name}</span>
        </div>
      }
    >
      <div className="mb-4">
        <Text type="secondary" className="text-sm">
          {module.description || '暂无模块描述'}
        </Text>
      </div>

      <div className="my-4">
        <span className="text-gray-600 font-medium text-sm border-b border-gray-200 pb-2 block">功能列表</span>
      </div>

      {module.features && module.features.length > 0 ? (
        module.features.map((feature, index) => (
          <FeatureItem key={`${feature.name}-${index}`} feature={feature} index={index} />
        ))
      ) : (
        <Empty description="暂无功能" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Card>
  );
}
