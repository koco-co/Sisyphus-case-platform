import { screen } from '@testing-library/react'

import PreprocessStatusCard from './PreprocessStatusCard'
import { createWrapper } from '../../../test/utils'

describe('PreprocessStatusCard', () => {
  it('renders the current preprocessing stage', () => {
    createWrapper(
      <PreprocessStatusCard
        status="ready_for_structuring"
        currentStage="structuring"
        summary="已抽取 3 个段落，待进入结构化"
      />,
    )

    expect(screen.getByText('预处理状态')).toBeInTheDocument()
    expect(screen.getByText('ready_for_structuring')).toBeInTheDocument()
    expect(screen.getByText('已抽取 3 个段落，待进入结构化')).toBeInTheDocument()
  })
})
