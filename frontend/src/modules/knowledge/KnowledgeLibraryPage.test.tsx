import { screen } from '@testing-library/react'

import KnowledgeLibraryPage from './pages/KnowledgeLibraryPage'
import { createWrapper } from '../../test/utils'

describe('KnowledgeLibraryPage', () => {
  it('renders the knowledge asset management page', () => {
    createWrapper(<KnowledgeLibraryPage />)

    expect(screen.getByText('知识库管理')).toBeInTheDocument()
    expect(screen.getByText('知识资产列表')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '升级为精选资产' })).toBeInTheDocument()
  })
})
