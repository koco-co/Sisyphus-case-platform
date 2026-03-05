import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import FileUploadButton from './FileUploadButton'

// Mock antd message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return {
    ...actual,
    message: {
      error: vi.fn(),
    },
  }
})

describe('FileUploadButton', () => {
  const mockOnUpload = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render upload button', () => {
    render(<FileUploadButton onUpload={mockOnUpload} />)

    // 检查按钮存在
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('should have correct accept attribute', () => {
    render(<FileUploadButton onUpload={mockOnUpload} />)

    // 检查文件输入存在
    const fileInput = document.querySelector('input[type="file"]')
    expect(fileInput).toHaveAttribute('accept', '.md,.txt,.pdf')
  })

  it('should call onUpload when file is selected', async () => {
    render(<FileUploadButton onUpload={mockOnUpload} />)

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith(file)
    })
  })

  it('should show error when file is too large', async () => {
    const { message } = await import('antd')

    render(<FileUploadButton onUpload={mockOnUpload} />)

    // 创建一个超过 10MB 的文件（模拟）
    const largeFile = {
      name: 'large.txt',
      size: 11 * 1024 * 1024, // 11MB
      type: 'text/plain',
    } as File

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement

    fireEvent.change(fileInput, { target: { files: [largeFile] } })

    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('文件大小不能超过 10MB')
    })
    expect(mockOnUpload).not.toHaveBeenCalled()
  })

  it('should be disabled when disabled prop is true', () => {
    render(<FileUploadButton onUpload={mockOnUpload} disabled />)

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    expect(fileInput).toBeDisabled()
  })
})
