import { useParams } from 'react-router-dom';
import { Typography } from 'antd';

const { Title } = Typography;

export default function ProjectDetail() {
  const params = useParams();
  const id = params.id;

  return (
    <div>
      <Title level={2}>项目详情</Title>
      <p>项目 ID: {id}</p>
    </div>
  );
}
