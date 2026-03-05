import { useState } from 'react';
import { Modal, Form, Input, Select, Button, Table, Space, Tag, message, Card, Checkbox } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useExportTemplates, useCreateExportTemplate } from '../../hooks/useExport';
import type { ExportTemplate } from '../../hooks/useExport';

interface FieldConfig {
  fields: string[];
}

const AVAILABLE_FIELDS = [
  { key: 'title', label: '用例标题' },
  { key: 'priority', label: '优先级' },
  { key: 'preconditions', label: '前置条件' },
  { key: 'steps', label: '测试步骤' },
  { key: 'tags', label: '标签' },
];

const PRIORITIES = ['P0', 'P1', 'P2', 'P3'];

export default function TemplateManager() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ExportTemplate | null>(null);
  const [form] = Form.useForm();

  const { data: templates, isLoading } = useExportTemplates();
  const createTemplate = useCreateExportTemplate();

  const handleCreateTemplate = () => {
    setEditingTemplate(null);
    setIsModalOpen(true);
    form.resetFields();
  };

  const handleEditTemplate = (template: ExportTemplate) => {
    setEditingTemplate(template);
    setIsModalOpen(true);
    form.setFieldsValue({
      name: template.name,
      fieldConfig: template.fieldConfig,
      formatConfig: template.formatConfig,
      filterConfig: template.filterConfig,
      isDefault: template.isDefault,
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await createTemplate.mutateAsync(values);
      setIsModalOpen(false);
      message.success(editingTemplate ? '模板已更新' : '模板已创建');
    } catch (error) {
      message.error('保存失败');
    }
  };

  const columns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '默认',
      dataIndex: 'isDefault',
      key: 'isDefault',
      render: (isDefault: boolean) => isDefault ? <Tag color="blue">默认</Tag> : null,
    },
    {
      title: '导出字段',
      dataIndex: 'fieldConfig',
      key: 'fieldConfig',
      render: (fieldConfig: FieldConfig) => (
        <Space size="small" wrap>
          {fieldConfig?.fields?.map((f: string) => (
            <Tag key={f}>{AVAILABLE_FIELDS.find((af) => af.key === f)?.label || f}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: ExportTemplate) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditTemplate(record)}
          />
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="导出模板管理"
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreateTemplate}
        >
          新建模板
        </Button>
      }
    >
      <Table
        dataSource={templates}
        columns={columns}
        loading={isLoading}
        rowKey="id"
      />

      <Modal
        title={editingTemplate ? '编辑模板' : '新建模板'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={handleSubmit}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item name="fieldConfig" label="导出字段">
            <Checkbox.Group>
              {AVAILABLE_FIELDS.map((f) => (
                <Checkbox key={f.key} value={f.key}>
                  {f.label}
                </Checkbox>
              ))}
            </Checkbox.Group>
          </Form.Item>

          <Form.Item name="delimiter" label="分隔符">
            <Select>
              <Select.Option value=",">逗号 (,)</Select.Option>
              <Select.Option value=";">分号 (;)</Select.Option>
              <Select.Option value="\t">制表符 (Tab)</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="priority" label="过滤优先级">
            <Checkbox.Group>
              {PRIORITIES.map((p) => (
                <Checkbox key={p} value={p}>
                  {p}
                </Checkbox>
              ))}
            </Checkbox.Group>
          </Form.Item>

          <Form.Item name="isDefault" valuePropName="checked" hidden>
            <Checkbox />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
