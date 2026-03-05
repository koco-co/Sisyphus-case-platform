import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatInput from './ChatInput'

describe('ChatInput', () => {
  const mockOnSend = vi.fn()
  const mockOnFileUpload = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render input textarea with default placeholder', () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    expect(screen.getByPlaceholderText('描述你想要生成的测试用例...')).toBeInTheDocument()
  })

  it('should render send button', () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    // 发送按钮是一个 icon-only 按钮
    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeInTheDocument()
  })

  it('should call onSend when send button clicked', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const textarea = screen.getByPlaceholderText('描述你想要生成的测试用例...')
    fireEvent.change(textarea, { target: { value: 'Test message' } })

    const sendButton = screen.getByRole('button', { name: /send/i })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockOnSend).toHaveBeenCalledWith('Test message', [])
    })
  })

  it('should be disabled when disabled prop is true', () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} disabled />)

    const textarea = screen.getByPlaceholderText('描述你想要生成的测试用例...')
    expect(textarea).toBeDisabled()
  })

  it('should show custom placeholder', () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} placeholder="Custom placeholder" />)

    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument()
  })

  it('should clear input after sending', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const textarea = screen.getByPlaceholderText('描述你想要生成的测试用例...') as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: 'Test message' } })

    const sendButton = screen.getByRole('button', { name: /send/i })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(textarea.value).toBe('')
    })
  })

  it('should not send empty message', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const sendButton = screen.getByRole('button', { name: /send/i })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockOnSend).not.toHaveBeenCalled()
    })
  })

  it('should send message on Enter key', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const textarea = screen.getByPlaceholderText('描述你想要生成的测试用例...')
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    await waitFor(() => {
      expect(mockOnSend).toHaveBeenCalledWith('Test message', [])
    })
  })

  it('should not send message on Shift+Enter', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const textarea = screen.getByPlaceholderText('描述你想要生成的测试用例...')
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })

    // 等待一下确保 onSend 没有被调用
    await new Promise(resolve => setTimeout(resolve, 100))
    expect(mockOnSend).not.toHaveBeenCalled()
  })

  it('should handle file upload', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(mockOnFileUpload).toHaveBeenCalled()
    })
  })

  it('should display uploaded file', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument()
    })
  })

  it('should display file size', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    // 创建一个 1.5KB 的文件
    const content = new Array(1536).fill('a').join('')
    const file = new File([content], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText(/\(1.5 KB\)/)).toBeInTheDocument()
    })
  })

  it('should remove file when remove button clicked', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('test.txt')).toBeInTheDocument()
    })

    // 点击删除按钮
    const removeButton = screen.getByText('×')
    fireEvent.click(removeButton)

    await waitFor(() => {
      expect(screen.queryByText('test.txt')).not.toBeInTheDocument()
    })
  })

  it('should send files along with message', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [file] } })

    const textarea = screen.getByPlaceholderText('描述你想要生成的测试用例...')
    fireEvent.change(textarea, { target: { value: 'Test message' } })

    const sendButton = screen.getByRole('button', { name: /send/i })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockOnSend).toHaveBeenCalledWith(
        'Test message',
        expect.arrayContaining([
          expect.objectContaining({
            name: 'test.txt',
            file: file,
          }),
        ])
      )
    })
  })

  it('should clear files after sending', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [file] } })

    const textarea = screen.getByPlaceholderText('描述你想要生成的测试用例...')
    fireEvent.change(textarea, { target: { value: 'Test message' } })

    const sendButton = screen.getByRole('button', { name: /send/i })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.queryByText('test.txt')).not.toBeInTheDocument()
    })
  })

  it('should enable send button when only files are attached', async () => {
    render(<ChatInput onSend={mockOnSend} onFileUpload={mockOnFileUpload} />)

    // 没有文件时，发送按钮应该是禁用的
    const sendButton = screen.getByRole('button', { name: /send/i })
    expect(sendButton).toBeDisabled()

    // 上传文件
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(sendButton).not.toBeDisabled()
    })
  })
})
