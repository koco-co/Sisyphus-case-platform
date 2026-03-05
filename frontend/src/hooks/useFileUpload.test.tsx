import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useFileUpload } from './useFileUpload'

// Mock axios
vi.mock('axios', () => {
  const mockPost = vi.fn()
  return {
    default: {
      create: () => ({
        post: mockPost,
        get: vi.fn(),
      }),
      _mockPost: mockPost,
    },
  }
})

// 创建 wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have uploadFile function', () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    })

    expect(result.current.uploadFile).toBeDefined()
    expect(typeof result.current.uploadFile).toBe('function')
  })

  it('should have uploadProgress', () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    })

    expect(result.current.uploadProgress).toBeDefined()
  })
})
