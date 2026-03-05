import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useFileUpload } from './useFileUpload'

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

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      post: vi.fn(),
      get: vi.fn(),
    }),
  },
}))

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

  it('should have uploadProgress with initial state', () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    })

    expect(result.current.uploadProgress).toBeDefined()
    expect(result.current.uploadProgress.loading).toBe(false)
    expect(result.current.uploadProgress.progress).toBe(0)
    expect(result.current.uploadProgress.error).toBeNull()
  })

  it('should have reset function', () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    })

    expect(result.current.reset).toBeDefined()
    expect(typeof result.current.reset).toBe('function')
  })

  it('should reset upload progress', () => {
    const { result } = renderHook(() => useFileUpload(), {
      wrapper: createWrapper(),
    })

    act(() => {
      result.current.reset()
    })

    expect(result.current.uploadProgress.loading).toBe(false)
    expect(result.current.uploadProgress.progress).toBe(0)
    expect(result.current.uploadProgress.error).toBeNull()
  })
})
