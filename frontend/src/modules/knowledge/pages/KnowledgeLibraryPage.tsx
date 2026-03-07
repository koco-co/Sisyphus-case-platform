import { Space, Typography } from 'antd'

import KnowledgeAssetTable from '../components/KnowledgeAssetTable'
import PromoteAssetButton from '../components/PromoteAssetButton'

const { Title, Paragraph } = Typography

export default function KnowledgeLibraryPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>知识库管理</Title>
        <Paragraph>管理从发布测试包回流的高质量资产，并逐步提升为精选层。</Paragraph>
      </div>
      <Space>
        <PromoteAssetButton />
      </Space>
      <KnowledgeAssetTable />
    </div>
  )
}
