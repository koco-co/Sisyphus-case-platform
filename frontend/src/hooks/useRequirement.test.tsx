import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useRequirement } from './useRequirement'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
    }),
  },
}))

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

describe('useRequirement', () => {
  it('should return query object', () => {
    const { result } = renderHook(() => useRequirement('test-id'), {
      wrapper: createWrapper(),
    })

    expect(result.current).toBeDefined()
    expect(result.current.isLoading).toBeDefined()
    expect(result.current.isFetching).toBeDefined()
  })

  it('should be disabled when id is empty', () => {
    const { result } = renderHook(() => useRequirement(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
  })

  it('should be disabled when id is null', () => {
    const { result } = renderHook(() => useRequirement(null as unknown as string), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
  })
})
