import { Button, Space, Typography } from 'antd'
import { Link } from 'react-router-dom'

const { Title, Paragraph } = Typography

export default function Home() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>Sisyphus 工作台入口</Title>
        <Paragraph>旧首页已收敛为新的阶段式工作台入口，请从下方快捷入口继续操作。</Paragraph>
      </div>
      <Space wrap>
        <Button type="primary">
          <Link to="/intake">进入需求导入</Link>
        </Button>
        <Button>
          <Link to="/review">进入覆盖发布</Link>
        </Button>
      </Space>
    </div>
  )
}
