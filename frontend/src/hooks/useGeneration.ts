import { useState, useCallback, useRef } from 'react';

export interface GenerationProgress {
  stage: 'idle' | 'connecting' | 'retrieving' | 'generating' | 'reviewing' | 'completed' | 'error';
  message: string;
  progress: number;
}

export interface TestCase {
  id?: string;
  title: string;
  priority: string;
  preconditions: string;
  steps: Array<{
    step: number;
    action: string;
    expected: string;
  }>;
  tags?: string[];
}

export interface GenerationResult {
  success: boolean;
  testCases: TestCase[];
  reviewPassed: boolean;
  attempts: number;
}

export function useGeneration() {
  const [progress, setProgress] = useState<GenerationProgress>({
    stage: 'idle',
    message: '',
    progress: 0,
  });
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const wsUrl = `ws://localhost:8000/api/generate/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setProgress({
        stage: 'connecting',
        message: '已连接到服务器',
        progress: 5,
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setProgress({
          stage: data.stage || 'generating',
          message: data.message || '',
          progress: data.progress || 0,
        });

        if (data.stage === 'completed') {
          setResult({
            success: true,
            testCases: data.test_cases || [],
            reviewPassed: data.review_passed || false,
            attempts: data.attempts || 1,
          });
          setIsGenerating(false);
        } else if (data.stage === 'error') {
          setResult({
            success: false,
            testCases: [],
            reviewPassed: false,
            attempts: 0,
          });
          setIsGenerating(false);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setProgress({
        stage: 'error',
        message: '连接错误',
        progress: 0,
      });
      setIsGenerating(false);
    };

    ws.onclose = () => {
      wsRef.current = null;
    };
  }, []);

  const generate = useCallback(
    async (requirement: string, options: {
      testPoints?: string[];
      projectId?: number;
      useRag?: boolean;
    } = {}) => {
      setIsGenerating(true);
      setResult(null);
      setProgress({
        stage: 'idle',
        message: '准备生成...',
        progress: 0,
      });

      connect();

      // Wait for connection and send request
      const sendRequest = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              requirement,
              test_points: options.testPoints || [],
              project_id: options.projectId,
              use_rag: options.useRag ?? true,
            })
          );
        } else if (wsRef.current?.readyState === WebSocket.CONNECTING) {
          setTimeout(sendRequest, 100);
        } else {
          // Reconnect if closed
          connect();
          setTimeout(sendRequest, 100);
        }
      };

      setTimeout(sendRequest, 100);
    },
    [connect]
  );

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsGenerating(false);
    setProgress({
      stage: 'idle',
      message: '已取消',
      progress: 0,
    });
  }, []);

  const reset = useCallback(() => {
    setProgress({
      stage: 'idle',
      message: '',
      progress: 0,
    });
    setResult(null);
    setIsGenerating(false);
  }, []);

  return {
    progress,
    result,
    isGenerating,
    generate,
    cancel,
    reset,
  };
}
