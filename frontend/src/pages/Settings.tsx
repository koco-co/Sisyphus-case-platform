import { Typography, Form, Input, Button, Card, Select } from 'antd';

const { Title } = Typography;
const { Option } = Select;

export default function Settings() {
  const [form] = Form.useForm();

  const onFinish = (values: any) => {
    console.log('Settings saved:', values);
  };

  return (
    <div>
      <Title level={2}>系统设置</Title>

      <Card title="LLM 配置" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            provider: 'openai',
          }}
        >
          <Form.Item
            label="LLM 提供商"
            name="provider"
            rules={[{ required: true, message: '请选择 LLM 提供商' }]}
          >
            <Select>
              <Option value="openai">OpenAI</Option>
              <Option value="azure">Azure OpenAI</Option>
              <Option value="anthropic">Anthropic</Option>
              <Option value="qwen">阿里百炼</Option>
              <Option value="zhipu">智谱 AI</Option>
              <Option value="minimax">MiniMax</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="API Key"
            name="apiKey"
            rules={[{ required: true, message: '请输入 API Key' }]}
          >
            <Input.Password placeholder="请输入 API Key" />
          </Form.Item>

          <Form.Item
            label="Base URL"
            name="baseUrl"
          >
            <Input placeholder="请输入 Base URL（可选）" />
          </Form.Item>

          <Form.Item
            label="模型"
            name="model"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="例如: gpt-4, claude-3-opus-20240229" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit">
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="向量数据库配置">
        <Form layout="vertical">
          <Form.Item label="向量数据库类型">
            <Select defaultValue="chroma">
              <Option value="chroma">Chroma</Option>
              <Option value="faiss">FAISS</Option>
              <Option value="pinecone">Pinecone</Option>
            </Select>
          </Form.Item>

          <Form.Item label="持久化路径">
            <Input placeholder="./data/vectors" />
          </Form.Item>

          <Form.Item>
            <Button type="primary">保存配置</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
