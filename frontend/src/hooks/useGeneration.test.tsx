import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useGeneration } from './useGeneration'

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

  constructor(public url: string) {}
}

vi.stubGlobal('WebSocket', MockWebSocket)

describe('useGeneration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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

  it('should cancel generation', () => {
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
  })
})
