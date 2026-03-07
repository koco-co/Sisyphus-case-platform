import { screen } from '@testing-library/react'

import TestPointPage from './pages/TestPointPage'
import { createWrapper } from '../../test/utils'

describe('TestPointPage', () => {
  it('renders the tree and detail regions', () => {
    createWrapper(<TestPointPage />)

    expect(screen.getByText('测试点设计')).toBeInTheDocument()
    expect(screen.getByText('测试点树')).toBeInTheDocument()
    expect(screen.getByText('测试点详情')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'AI 查漏' })).toBeInTheDocument()
  })
})
