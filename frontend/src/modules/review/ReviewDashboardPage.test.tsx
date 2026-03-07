import { screen } from '@testing-library/react'

import ReviewDashboardPage from './pages/ReviewDashboardPage'
import { createWrapper } from '../../test/utils'

describe('ReviewDashboardPage', () => {
  it('renders coverage and publish controls', () => {
    createWrapper(<ReviewDashboardPage />)

    expect(screen.getByText('覆盖分析与发布')).toBeInTheDocument()
    expect(screen.getByText('覆盖矩阵')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '发布测试包' })).toBeInTheDocument()
  })
})
