import { Button, Space } from 'antd'

export default function PublishBar() {
  return (
    <Space>
      <Button type="primary">发布测试包</Button>
      <Button>退回修改</Button>
    </Space>
  )
}
