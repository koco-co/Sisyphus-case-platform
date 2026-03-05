import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useGeneration } from './useGeneration'

// 存储 WebSocket 实例以便在测试中访问
let wsInstance: {
  readyState: number
  onopen: ((event: Event) => void) | null
  onclose: ((event: CloseEvent) => void) | null
  onmessage: ((event: MessageEvent) => void) | null
  onerror: ((event: Event) => void) | null
  send: ReturnType<typeof vi.fn>
  close: ReturnType<typeof vi.fn>
} | null = null

// Mock WebSocket with class syntax
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.OPEN
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  send = vi.fn()
  close = vi.fn()

  constructor(public url: string) {
    wsInstance = this
  }
}

vi.stubGlobal('WebSocket', MockWebSocket)

describe('useGeneration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    wsInstance = null
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should have initial idle state', () => {
    const { result } = renderHook(() => useGeneration())

    expect(result.current.progress.stage).toBe('idle')
    expect(result.current.isGenerating).toBe(false)
    expect(result.current.result).toBeNull()
  })

  it('should have generate function', () => {
    const { result } = renderHook(() => useGeneration())

    expect(result.current.generate).toBeDefined()
    expect(typeof result.current.generate).toBe('function')
  })

  it('should have cancel function', () => {
    const { result } = renderHook(() => useGeneration())

    expect(result.current.cancel).toBeDefined()
    expect(typeof result.current.cancel).toBe('function')
  })

  it('should have reset function', () => {
    const { result } = renderHook(() => useGeneration())

    expect(result.current.reset).toBeDefined()
    expect(typeof result.current.reset).toBe('function')
  })

  it('should reset to idle state', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.reset()
    })

    expect(result.current.progress.stage).toBe('idle')
    expect(result.current.isGenerating).toBe(false)
  })

  it('should start generation', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    expect(result.current.isGenerating).toBe(true)
  })

  it('should update progress on WebSocket open', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    // 模拟 WebSocket 打开
    act(() => {
      if (wsInstance?.onopen) {
        wsInstance.onopen(new Event('open'))
      }
    })

    expect(result.current.progress.stage).toBe('connecting')
    expect(result.current.progress.message).toBe('已连接到服务器')
    expect(result.current.progress.progress).toBe(5)
  })

  it('should handle completed stage with test cases', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    // 模拟 WebSocket 打开
    act(() => {
      if (wsInstance?.onopen) {
        wsInstance.onopen(new Event('open'))
      }
    })

    // 模拟完成消息
    act(() => {
      if (wsInstance?.onmessage) {
        wsInstance.onmessage(new MessageEvent('message', {
          data: JSON.stringify({
            stage: 'completed',
            message: '生成完成',
            progress: 100,
            test_cases: [
              { title: 'Test 1', priority: 'P0', preconditions: '', steps: [] }
            ],
            review_passed: true,
            attempts: 2,
          })
        }))
      }
    })

    expect(result.current.result?.success).toBe(true)
    expect(result.current.result?.reviewPassed).toBe(true)
    expect(result.current.result?.attempts).toBe(2)
    expect(result.current.result?.testCases).toHaveLength(1)
    expect(result.current.isGenerating).toBe(false)
  })

  it('should handle error stage', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    // 模拟错误消息
    act(() => {
      if (wsInstance?.onmessage) {
        wsInstance.onmessage(new MessageEvent('message', {
          data: JSON.stringify({
            stage: 'error',
            message: '生成失败',
            progress: 0,
          })
        }))
      }
    })

    expect(result.current.result?.success).toBe(false)
    expect(result.current.result?.testCases).toHaveLength(0)
    expect(result.current.isGenerating).toBe(false)
  })

  it('should handle WebSocket error', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    // 模拟 WebSocket 错误
    act(() => {
      if (wsInstance?.onerror) {
        wsInstance.onerror(new Event('error'))
      }
    })

    expect(result.current.progress.stage).toBe('error')
    expect(result.current.progress.message).toBe('连接错误')
    expect(result.current.isGenerating).toBe(false)
  })

  it('should handle WebSocket close', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    expect(wsInstance).not.toBeNull()

    // 模拟 WebSocket 关闭
    act(() => {
      if (wsInstance?.onclose) {
        wsInstance.onclose(new CloseEvent('close'))
      }
    })

    // WebSocket 引用应该被清除
    // 再次调用 cancel 应该不会出错
    act(() => {
      result.current.cancel()
    })

    expect(result.current.isGenerating).toBe(false)
  })

  it('should handle invalid JSON message', () => {
    const { result } = renderHook(() => useGeneration())
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    act(() => {
      result.current.generate('Test requirement')
    })

    // 模拟无效 JSON 消息
    act(() => {
      if (wsInstance?.onmessage) {
        wsInstance.onmessage(new MessageEvent('message', {
          data: 'invalid json'
        }))
      }
    })

    // 应该记录错误但不崩溃
    expect(consoleSpy).toHaveBeenCalled()
    expect(result.current.isGenerating).toBe(true)

    consoleSpy.mockRestore()
  })

  it('should cancel generation and close WebSocket', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    expect(result.current.isGenerating).toBe(true)

    act(() => {
      result.current.cancel()
    })

    expect(result.current.isGenerating).toBe(false)
    expect(result.current.progress.stage).toBe('idle')
    expect(result.current.progress.message).toBe('已取消')
    expect(wsInstance?.close).toHaveBeenCalled()
  })

  it('should send request when WebSocket is open', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement', {
        testPoints: ['point1', 'point2'],
        projectId: 123,
        useRag: false,
      })
    })

    // 模拟 WebSocket 打开
    act(() => {
      if (wsInstance?.onopen) {
        wsInstance.onopen(new Event('open'))
      }
    })

    // 推进定时器以触发 sendRequest
    act(() => {
      vi.advanceTimersByTime(150)
    })

    // 检查 send 是否被调用
    expect(wsInstance?.send).toHaveBeenCalled()
  })

  it('should handle generating stage message', () => {
    const { result } = renderHook(() => useGeneration())

    act(() => {
      result.current.generate('Test requirement')
    })

    // 模拟生成中的消息
    act(() => {
      if (wsInstance?.onmessage) {
        wsInstance.onmessage(new MessageEvent('message', {
          data: JSON.stringify({
            stage: 'generating',
            message: '正在生成测试用例...',
            progress: 50,
          })
        }))
      }
    })

    expect(result.current.progress.stage).toBe('generating')
    expect(result.current.progress.message).toBe('正在生成测试用例...')
    expect(result.current.progress.progress).toBe(50)
    expect(result.current.isGenerating).toBe(true)
  })
})
