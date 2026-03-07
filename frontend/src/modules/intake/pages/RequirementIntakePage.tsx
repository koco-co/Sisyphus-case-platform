import { useMemo, useState } from 'react'
import { Button, Card, Col, Row, Space, Typography, message } from 'antd'

import { createTask, uploadTaskDocument } from '../api'
import TaskMetaForm, { type TaskMetaValues } from '../components/TaskMetaForm'
import UploadPanel from '../components/UploadPanel'

const { Title, Paragraph, Text } = Typography

const initialValue: TaskMetaValues = {
  title: '',
  projectId: 1,
  sourceType: 'pdf',
  businessDomain: '',
}

export default function RequirementIntakePage() {
  const [taskMeta, setTaskMeta] = useState<TaskMetaValues>(initialValue)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const canSubmit = useMemo(() => {
    return Boolean(taskMeta.title.trim() && taskMeta.projectId > 0 && selectedFile)
  }, [selectedFile, taskMeta.projectId, taskMeta.title])

  const handleSubmit = async () => {
    if (!canSubmit || !selectedFile) {
      void message.warning('请先填写任务信息并选择需求文件')
      return
    }

    setIsSubmitting(true)
    try {
      const task = await createTask({
        project_id: taskMeta.projectId,
        title: taskMeta.title,
        source_type: taskMeta.sourceType,
        business_domain: taskMeta.businessDomain || undefined,
      })

      await uploadTaskDocument(task.id, selectedFile)
      void message.success('需求任务已创建，并完成文档挂载')
    } catch {
      void message.error('创建需求任务失败，请稍后重试')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <Title level={2}>需求导入</Title>
        <Paragraph>
          从文档、Markdown 或后续 OCR / 语音转写入口创建新的测试设计任务。
        </Paragraph>
      </div>

      <Row gutter={16}>
        <Col span={10}>
          <Card title="任务信息">
            <TaskMetaForm value={taskMeta} onChange={setTaskMeta} />
          </Card>
        </Col>
        <Col span={14}>
          <Card title="需求文档上传">
            <Space orientation="vertical" className="w-full" size="middle">
              <UploadPanel onSelectFile={setSelectedFile} />
              <Text type="secondary">
                当前选择：{selectedFile ? selectedFile.name : '尚未选择文件'}
              </Text>
            </Space>
          </Card>
        </Col>
      </Row>

      <Button type="primary" onClick={handleSubmit} loading={isSubmitting} disabled={!canSubmit}>
        创建需求任务
      </Button>
    </div>
  )
}
