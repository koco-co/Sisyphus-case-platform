import { screen } from '@testing-library/react'
import { vi } from 'vitest'

import App from './App'
import { createWrapper } from './test/utils'

vi.mock('./components/Layout/AppSidebar', () => ({
  default: () => <div>Mock Sidebar</div>,
}))

vi.mock('./pages/Dashboard', () => ({
  default: () => <div>Mock Dashboard Page</div>,
}))

vi.mock('./pages/Settings', () => ({
  default: () => <div>Mock Settings Page</div>,
}))

vi.mock('./modules/intake/pages/RequirementIntakePage', () => ({
  default: () => <div>Mock Intake Page</div>,
}))

vi.mock('./modules/requirement/pages/RequirementStructurePage', () => ({
  default: () => <div>Mock Structure Page</div>,
}))

vi.mock('./modules/test-points/pages/TestPointPage', () => ({
  default: () => <div>Mock Test Point Page</div>,
}))

vi.mock('./modules/test-cases/pages/TestCaseWorkbenchPage', () => ({
  default: () => <div>Mock Case Workbench Page</div>,
}))

vi.mock('./modules/review/pages/ReviewDashboardPage', () => ({
  default: () => <div>Mock Review Page</div>,
}))

vi.mock('./modules/knowledge/pages/KnowledgeLibraryPage', () => ({
  default: () => <div>Mock Knowledge Page</div>,
}))

vi.mock('./modules/integrations/pages/IntegrationSettingsPage', () => ({
  default: () => <div>Mock Integration Page</div>,
}))

describe('App', () => {
  it('renders the default route inside the application shell', async () => {
    createWrapper(<App />)

    expect(await screen.findByText('Mock Sidebar')).toBeInTheDocument()
    expect(await screen.findByText('Mock Dashboard Page')).toBeInTheDocument()
  })
})
