import { useState, useCallback } from 'react';
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface UploadedFileInfo {
  id: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  parsedContent: string;
  createdAt: string;
}

export interface UploadProgress {
  loading: boolean;
  progress: number;
  error: string | null;
}

export function useFileUpload() {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    loading: false,
    progress: 0,
    error: null,
  });

  const uploadFile = useCallback(async (file: File): Promise<UploadedFileInfo | null> => {
    setUploadProgress({
      loading: true,
      progress: 0,
      error: null,
    });

    try {
      const formData = new FormData();
      formData.append('upload_file', file);

      const response = await api.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress((prev) => ({
            ...prev,
            progress,
          }));
        },
      });

      setUploadProgress({
        loading: false,
        progress: 100,
        error: null,
      });

      return {
        id: response.data.file.id,
        filename: response.data.file.filename,
        originalName: response.data.file.original_name,
        mimeType: response.data.file.mime_type,
        size: response.data.file.size,
        parsedContent: response.data.parsed_content,
        createdAt: response.data.file.created_at,
      };
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '上传失败';
      setUploadProgress({
        loading: false,
        progress: 0,
        error: errorMessage,
      });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setUploadProgress({
      loading: false,
      progress: 0,
      error: null,
    });
  }, []);

  return {
    uploadProgress,
    uploadFile,
    reset,
  };
}
