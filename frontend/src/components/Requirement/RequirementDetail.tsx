import { Typography, Empty, Spin } from 'antd';
import ModuleCard from './ModuleCard';
import type { Requirement } from '../../hooks/useRequirement';

const { Title, Paragraph } = Typography;

interface RequirementDetailProps {
  requirement: Requirement | undefined;
  loading: boolean;
}

export default function RequirementDetail({ requirement, loading }: RequirementDetailProps) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Spin size="large" tip="加载需求数据..." />
      </div>
    );
  }

  if (!requirement) {
    return (
      <Empty
        description="未找到需求"
        className="py-20"
      />
    );
  }

  return (
    <div>
      {/* 需求标题 */}
      <div className="mb-6">
        <Title level={3} className="mb-2">
          {requirement.title}
        </Title>
        <Paragraph type="secondary" className="text-sm">
          创建时间: {new Date(requirement.createdAt).toLocaleString('zh-CN')}
          {' | '}
          更新时间: {new Date(requirement.updatedAt).toLocaleString('zh-CN')}
        </Paragraph>
      </div>

      {/* 模块列表 */}
      {requirement.content?.modules && requirement.content.modules.length > 0 ? (
        requirement.content.modules.map((module, index) => (
          <ModuleCard key={`${module.name}-${index}`} module={module} moduleIndex={index} />
        ))
      ) : (
        <Empty description="暂无模块数据" className="py-10" />
      )}
    </div>
  );
}
