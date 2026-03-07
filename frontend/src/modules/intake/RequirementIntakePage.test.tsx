import { screen } from '@testing-library/react'

import RequirementIntakePage from './pages/RequirementIntakePage'
import { createWrapper } from '../../test/utils'

describe('RequirementIntakePage', () => {
  it('renders the intake form and upload panel', () => {
    createWrapper(<RequirementIntakePage />)

    expect(screen.getByText('需求导入')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('请输入需求名称')).toBeInTheDocument()
    expect(screen.getByText('点击或拖拽上传需求文档')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '创建需求任务' })).toBeDisabled()
  })
})
