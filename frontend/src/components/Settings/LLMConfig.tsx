import { useEffect } from 'react';
import { Form, Select, Input, Button, message, Spin, Typography } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

interface LLMConfigType {
  provider: string;
  apiKey: string;
  model: string;
}

interface ProviderInfo {
  name: string;
  models: string[];
}

type Providers = Record<string, ProviderInfo>;

const { Text } = Typography;

export default function LLMConfig() {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch providers list
  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: async () => {
      const response = await api.get<Providers>('/config/providers');
      return response.data;
    },
  });

  // Fetch current LLM config
  const { data: config, isLoading } = useQuery({
    queryKey: ['llm-config'],
    queryFn: async () => {
      const response = await api.get<LLMConfigType>('/config/llm');
      return response.data;
    },
  });

  // Update config mutation
  const updateConfig = useMutation({
    mutationFn: async (values: LLMConfigType) => {
      const response = await api.put<LLMConfigType>('/config/llm', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('配置已保存');
      queryClient.invalidateQueries({ queryKey: ['llm-config'] });
    },
    onError: (error: Error) => {
      message.error(`保存失败: ${error.message}`);
    },
  });

  // Set form values when config is loaded
  useEffect(() => {
    if (config) {
      form.setFieldsValue({
        provider: config.provider,
        model: config.model,
        apiKey: '',
      });
    }
  }, [config, form]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <Spin />
      </div>
    );
  }

  const selectedProvider = Form.useWatch('provider', form) || config?.provider || 'openai';
  const providerModels = providers?.[selectedProvider]?.models || [];

  return (
    <div>
      <Form
        form={form}
        layout="vertical"
        initialValues={config}
        onFinish={(values) => updateConfig.mutate(values)}
        className="max-w-md"
      >
        <Form.Item
          name="provider"
          label="LLM 提供商"
          rules={[{ required: true, message: '请选择 LLM 提供商' }]}
        >
          <Select
            onChange={() => {
              // Reset model when provider changes
              form.setFieldValue('model', undefined);
            }}
          >
            {providers &&
              Object.entries(providers).map(([value, info]) => (
                <Select.Option key={value} value={value}>
                  {info.name}
                </Select.Option>
              ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="model"
          label="模型"
          rules={[{ required: true, message: '请选择模型' }]}
        >
          <Select>
            {providerModels.map((m) => (
              <Select.Option key={m} value={m}>
                {m}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="apiKey"
          label="API Key"
          extra={<Text type="secondary">留空则保持原有 API Key 不变</Text>}
        >
          <Input.Password placeholder="请输入 API Key（留空保持不变）" />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={updateConfig.isPending}
          >
            保存配置
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
}
