import { screen } from '@testing-library/react'

import TestCaseWorkbenchPage from './pages/TestCaseWorkbenchPage'
import { createWrapper } from '../../test/utils'

describe('TestCaseWorkbenchPage', () => {
  it('renders the case table and detail drawer entry points', () => {
    createWrapper(<TestCaseWorkbenchPage />)

    expect(screen.getByText('测试用例工作台')).toBeInTheDocument()
    expect(screen.getByText('测试用例列表')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '单条重生成' })).toBeInTheDocument()
  })
})
