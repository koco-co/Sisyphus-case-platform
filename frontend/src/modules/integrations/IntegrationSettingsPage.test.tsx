import { screen } from '@testing-library/react'

import IntegrationSettingsPage from './pages/IntegrationSettingsPage'
import { createWrapper } from '../../test/utils'

describe('IntegrationSettingsPage', () => {
  it('renders integration config and field mapping editor', () => {
    createWrapper(<IntegrationSettingsPage />)

    expect(screen.getByText('集成与导出')).toBeInTheDocument()
    expect(screen.getByText('字段映射')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '执行 Markdown 导出' })).toBeInTheDocument()
  })
})
