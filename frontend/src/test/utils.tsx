import React from 'react'
import { QueryClient, QueryClientProvider,
} from '@tanstack/react-query'
import { render,
} from '@testing-library/react'
import type { RenderOptions } from '@testing-library/react'

// 创建一个测试用的 QueryClient
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
}

// 创建一个带有 QueryClientProvider 的 wrapper
export function createWrapper<
  T extends React.ReactNode
>(ui: T,  options?: Omit<RenderOptions, 'wrapper'>
) {
  const queryClient = createTestQueryClient()

  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    ),
    ...options,
  })
}
