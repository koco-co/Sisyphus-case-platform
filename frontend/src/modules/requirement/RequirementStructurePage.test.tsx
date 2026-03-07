import { screen } from '@testing-library/react'

import RequirementStructurePage from './pages/RequirementStructurePage'
import { createWrapper } from '../../test/utils'

describe('RequirementStructurePage', () => {
  it('renders the source pane and structure editor', () => {
    createWrapper(<RequirementStructurePage />)

    expect(screen.getByText('需求结构化')).toBeInTheDocument()
    expect(screen.getByText('原始需求')).toBeInTheDocument()
    expect(screen.getByText('结构化结果')).toBeInTheDocument()
    expect(screen.getByText('待确认问题')).toBeInTheDocument()
  })
})
