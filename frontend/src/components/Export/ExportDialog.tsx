import { useState, useEffect } from 'react';
import { Modal, Form, Select, Checkbox, Button, Space, message, Divider, Spin } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

interface ExportField {
  key: string;
  label: string;
  required: boolean;
}

interface ExportTemplate {
  id: string;
  name: string;
  field_config: { fields: string[] };
  format_config: { delimiter: string; include_headers: boolean };
  is_default: boolean;
}

interface ExportDialogProps {
  open: boolean;
  testCaseIds: string[];
  onClose: () => void;
}

const DELIMITER_OPTIONS = [
  { value: ',', label: '逗号 (,)' },
  { value: ';', label: '分号 (;)' },
  { value: '\t', label: '制表符 (Tab)' },
  { value: '|', label: '竖线 (|)' },
];

const FORMAT_OPTIONS = [
  { value: 'csv', label: 'CSV 格式' },
  { value: 'json', label: 'JSON 格式' },
];

export default function ExportDialog({ open, testCaseIds, onClose }: ExportDialogProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fields, setFields] = useState<ExportField[]>([]);
  const [templates, setTemplates] = useState<ExportTemplate[]>([]);
  const [selectedFormat, setSelectedFormat] = useState('csv');

  useEffect(() => {
    if (open) {
      loadFields();
      loadTemplates();
    }
  }, [open]);

  const loadFields = async () => {
    try {
      const response = await api.get('/export/fields');
      setFields(response.data.fields);
    } catch (error) {
      console.error('Failed to load fields:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await api.get('/export/templates');
      setTemplates(response.data);

      // 设置默认模板
      const defaultTemplate = response.data.find((t: ExportTemplate) => t.is_default);
      if (defaultTemplate) {
        form.setFieldsValue({
          template_id: defaultTemplate.id,
          fields: defaultTemplate.field_config?.fields || ['title', 'priority', 'preconditions', 'steps'],
          delimiter: defaultTemplate.format_config?.delimiter || ',',
        });
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleTemplateChange = (templateId: string) => {
    const template = templates.find((t) => t.id === templateId);
    if (template) {
      form.setFieldsValue({
        fields: template.field_config?.fields || [],
        delimiter: template.format_config?.delimiter || ',',
      });
    }
  };

  const handleExport = async () => {
    try {
      const values = await form.validateFields();

      setLoading(true);

      const response = await api.post('/export/', {
        test_case_ids: testCaseIds,
        format: selectedFormat,
        template_id: values.template_id === 'default' ? null : values.template_id,
        field_config: {
          fields: values.fields || ['title', 'priority', 'preconditions', 'steps'],
        },
        format_config: {
          delimiter: values.delimiter || ',',
          include_headers: true,
        },
      }, {
        responseType: selectedFormat === 'csv' ? 'text' : 'json',
      });

      // 创建下载
      const blob = new Blob(
        [selectedFormat === 'csv' ? response.data : JSON.stringify(response.data, null, 2)],
        { type: selectedFormat === 'csv' ? 'text/csv' : 'application/json' }
      );
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `test_cases.${selectedFormat}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success(`成功导出 ${testCaseIds.length} 个测试用例`);
      onClose();
    } catch (error) {
      message.error('导出失败');
      console.error('Export error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={
        <Space>
          <DownloadOutlined />
          <span>导出测试用例</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="export"
          type="primary"
          icon={<DownloadOutlined />}
          loading={loading}
          onClick={handleExport}
        >
          导出 ({testCaseIds.length} 个用例)
        </Button>,
      ]}
      width={600}
    >
      <Spin spinning={fields.length === 0}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            format: 'csv',
            fields: ['title', 'priority', 'preconditions', 'steps'],
            delimiter: ',',
          }}
        >
          <Form.Item name="format" label="导出格式">
            <Select
              options={FORMAT_OPTIONS}
              onChange={setSelectedFormat}
            />
          </Form.Item>

          {templates.length > 0 && (
            <Form.Item name="template_id" label="使用模板">
              <Select
                placeholder="选择导出模板"
                onChange={handleTemplateChange}
                allowClear
              >
                {templates.map((t) => (
                  <Select.Option key={t.id} value={t.id}>
                    {t.name}
                    {t.is_default && ' (默认)'}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          )}

          <Divider>导出字段</Divider>

          <Form.Item name="fields" label="选择要导出的字段">
            <Checkbox.Group className="grid grid-cols-2 gap-2">
              {fields.map((field) => (
                <Checkbox
                  key={field.key}
                  value={field.key}
                  disabled={field.required}
                >
                  {field.label}
                  {field.required && <span className="text-gray-400 text-xs ml-1">(必选)</span>}
                </Checkbox>
              ))}
            </Checkbox.Group>
          </Form.Item>

          {selectedFormat === 'csv' && (
            <Form.Item name="delimiter" label="分隔符">
              <Select options={DELIMITER_OPTIONS} />
            </Form.Item>
          )}
        </Form>
      </Spin>
    </Modal>
  );
}
