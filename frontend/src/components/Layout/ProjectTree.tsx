import { Tree, Button, Empty, Spin, message } from 'antd';
import { FolderOutlined, FileTextOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import type { TreeDataNode } from 'antd';

import { useProjects, useCreateProject, type Project } from '../../hooks/useProjects';

interface ProjectTreeProps {
  onProjectCreated?: (project: Project) => void;
}

export default function ProjectTree({ onProjectCreated }: ProjectTreeProps) {
  const navigate = useNavigate();
  const { data: projects, isLoading, error } = useProjects();
  const createProject = useCreateProject();
  const [isCreating, setIsCreating] = useState(false);

  // Transform project data into tree structure
  const treeData: TreeDataNode[] = (projects || []).map((project) => ({
    key: `project-${project.id}`,
    title: project.name,
    icon: <FolderOutlined />,
    children:
      project.requirements?.map((req) => ({
        key: `requirement-${req.id}`,
        title: req.title,
        icon: <FileTextOutlined />,
        isLeaf: true,
      })) || [],
  }));

  const handleSelect = (selectedKeys: React.Key[]) => {
    if (selectedKeys.length === 0) return;

    const key = selectedKeys[0] as string;
    if (key.startsWith('requirement-')) {
      const id = key.replace('requirement-', '');
      navigate(`/requirements/${id}`);
    } else if (key.startsWith('project-')) {
      const id = key.replace('project-', '');
      navigate(`/projects/${id}`);
    }
  };

  const handleCreateProject = async () => {
    setIsCreating(true);
    try {
      const project = await createProject.mutateAsync({
        name: `新项目 ${new Date().toLocaleDateString('zh-CN')}`,
      });
      onProjectCreated?.(project);
      void message.success('项目创建成功');
    } catch {
      void message.error('项目创建失败，请重试');
    } finally {
      setIsCreating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Spin size="small" />
      </div>
    );
  }

  if (error) {
    return <div className="p-4 text-red-500 text-sm">加载失败，请刷新重试</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b border-gray-100">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={handleCreateProject}
          loading={isCreating}
        >
          新建项目
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-2">
        {treeData.length === 0 ? (
          <Empty description="暂无项目" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Tree
            showIcon
            treeData={treeData}
            onSelect={handleSelect}
            defaultExpandAll
            className="text-sm"
          />
        )}
      </div>
    </div>
  );
}
