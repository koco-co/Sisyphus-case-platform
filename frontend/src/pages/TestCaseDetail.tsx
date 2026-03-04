import { useParams } from 'react-router-dom';
import { Typography } from 'antd';

const { Title } = Typography;

export default function TestCaseDetail() {
  const params = useParams();
  const id = params.id;

  return (
    <div>
      <Title level={2}>测试用例详情</Title>
      <p>用例 ID: {id}</p>
    </div>
  );
}
