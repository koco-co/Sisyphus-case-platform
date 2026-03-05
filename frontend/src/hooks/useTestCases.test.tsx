import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useTestCases, useCreateTestCases, useTestCase } from './useTestCases'

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

describe('useTestCases', () => {
  it('should return query object', () => {
    const { result } = renderHook(() => useTestCases('test-id'), {
      wrapper: createWrapper(),
    })

    expect(result.current).toBeDefined()
    expect(result.current.isLoading).toBeDefined()
    expect(result.current.isFetching).toBeDefined()
  })

  it('should be disabled when id is empty', () => {
    const { result } = renderHook(() => useTestCases(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
  })
})

describe('useTestCase', () => {
  it('should return query object', () => {
    const { result } = renderHook(() => useTestCase('tc-1'), {
      wrapper: createWrapper(),
    })

    expect(result.current).toBeDefined()
    expect(result.current.isLoading).toBeDefined()
    expect(result.current.isFetching).toBeDefined()
  })

  it('should be disabled when id is empty', () => {
    const { result } = renderHook(() => useTestCase(''), {
      wrapper: createWrapper(),
    })

    expect(result.current.isFetching).toBe(false)
  })
})

describe('useCreateTestCases', () => {
  it('should have mutate function', () => {
    const { result } = renderHook(() => useCreateTestCases(), {
      wrapper: createWrapper(),
    })

    expect(result.current.mutate).toBeDefined()
    expect(result.current.mutateAsync).toBeDefined()
  })

  it('should have correct initial state', () => {
    const { result } = renderHook(() => useCreateTestCases(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isPending).toBe(false)
    expect(result.current.isError).toBe(false)
  })
})
