import { Form, Input, InputNumber, Select } from 'antd'

export interface TaskMetaValues {
  title: string
  projectId: number
  sourceType: string
  businessDomain?: string
}

interface TaskMetaFormProps {
  value: TaskMetaValues
  onChange: (value: TaskMetaValues) => void
}

export default function TaskMetaForm({ value, onChange }: TaskMetaFormProps) {
  return (
    <Form layout="vertical">
      <Form.Item label="需求名称" required>
        <Input
          placeholder="请输入需求名称"
          value={value.title}
          onChange={(event) => onChange({ ...value, title: event.target.value })}
        />
      </Form.Item>
      <Form.Item label="项目 ID" required>
        <InputNumber
          className="w-full"
          min={1}
          value={value.projectId}
          onChange={(projectId) => onChange({ ...value, projectId: projectId ?? 1 })}
        />
      </Form.Item>
      <Form.Item label="来源类型" required>
        <Select
          value={value.sourceType}
          onChange={(sourceType) => onChange({ ...value, sourceType })}
          options={[
            { label: 'Word / PDF', value: 'pdf' },
            { label: 'Markdown', value: 'md' },
            { label: '口述转写', value: 'speech' },
          ]}
        />
      </Form.Item>
      <Form.Item label="业务域">
        <Input
          placeholder="例如：结算中心 / 主数据 / 标签平台"
          value={value.businessDomain}
          onChange={(event) => onChange({ ...value, businessDomain: event.target.value })}
        />
      </Form.Item>
    </Form>
  )
}
