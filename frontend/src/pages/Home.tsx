import { useState, useCallback } from 'react';
import { message, Button, Modal, Select } from 'antd';

import ChatInput from '../components/Chat/ChatInput';
import StreamingMessage from '../components/Chat/StreamingMessage';
import FilePreview from '../components/Chat/FilePreview';
import ExportDialog from '../components/Export/ExportDialog';
import { useGeneration, useFileUpload, useCreateTestCases, useRequirement } from '../hooks';
import type { UploadedFile } from '../components/Chat/ChatInput';
import type { TestCase, UploadedFileInfo } from '../hooks';

interface FileWithContent extends UploadedFile {
  serverInfo?: UploadedFileInfo;
  parsedContent?: string;
  uploadProgress?: number;
  uploadError?: string;
}

export default function Home() {
  const [uploadedFiles, setUploadedFiles] = useState<FileWithContent[]>([]);
  const [generatedCases, setGeneratedCases] = useState<TestCase[]>([]);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [selectedRequirementId, setSelectedRequirementId] = useState<string | null>(null);

  const { progress, result, isGenerating, generate, cancel, reset } = useGeneration();
  const { uploadFile } = use useFileUpload();
  const createTestCases = useCreateTestCases();
  const { data: requirements } = useRequirement(selectedRequirementId || null);

  const handleSend = useCallback(
    (msg: string, _files: UploadedFile[]) => {
      // 获取所有已上传文件的内容
      const filesWithContent = uploadedFiles.filter(f => f.parsedContent);

      if (!msg.trim() && filesWithContent.length === 0) {
        message.warning('请输入需求描述或上传文件');
        return;
      }

      // 重置之前的结果
      setGeneratedCases([]);
      reset();

      // 构建需求内容
      let requirement = msg;

      // 添加文件内容到需求
      filesWithContent.forEach((f) => {
        if (f.parsedContent) {
          requirement += `\n\n---\n### 文件: ${f.name}\n\n${f.parsedContent}`;
        }
      });

      // 开始生成
      generate(requirement, {
        useRag: true,
      });
    },
    [uploadedFiles, generate, reset]
  );

  const handleFileUpload = useCallback(
    async (file: UploadedFile) => {
      // 添加到列表（显示加载状态)
      const fileWithContent: FileWithContent = {
        ...file,
        uploadProgress: 0,
      };
      setUploadedFiles((prev) => [...prev, fileWithContent]);

      // 上传到服务器
      const uploadResult = await uploadFile(file.file);

      if (uploadResult) {
        // 更新文件信息
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.uid === file.uid
              ? {
                  ...f,
                  serverInfo: uploadResult,
                  parsedContent: uploadResult.parsedContent,
                  uploadProgress: 100,
                }
              : f
          )
        );
      } else {
        // 标记上传失败
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.uid === file.uid
              ? {
                ...f,
                uploadProgress: 0,
                uploadError: '上传失败',
              }
              : f
          )
        );
      }
    },
    [uploadFile]
  );

  const handleRemoveFile = useCallback((uid: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.uid !== uid));
  }, []);

  const handleSaveCases = useCallback(async () => {
    if (!result?.testCases || result.testCases.length === 0) {
      return;
    }

    // 如果 no selected requirementId) {
      // Show requirement selection dialog
      setSaveDialogOpen(true);
      return;
    }

    // Check if requirement exists
    const requirement = requirements?.find((r) => r.id === selectedRequirementId);
    if (!requirement) {
      message.error('选择的需求不存在');
      return;
    }

    // Prepare test cases data
    const testCasesToSave = result.testCases.map((tc) => ({
      title: tc.title,
      priority: tc.priority,
      preconditions: tc.preconditions || '',
      steps: tc.steps || [],
      tags: tc.tags || [],
    }));

    // Save to database
    try {
      const savedCases = await createTestCases({
        requirementId: selectedRequirementId,
        testCases: testCasesToSave,
      });
      message.success(`已保存 ${savedCases.length} 个测试用例到需求: ${requirement.title}`);
      setSaveDialogOpen(false);
    } catch (error) {
      message.error('保存失败，请重试');
      console.error('Save error:', error);
    }
  }, [result, selectedRequirementId, createTestCases, requirements]);

  const handleExportCases = useCallback(() => {
    if (result?.testCases && result.testCases.length > 0) {
      setExportDialogOpen(true);
    }
  }, [result]);

  const getTestCaseIds = useCallback(() => {
    // 从生成的用例中获取 ID 列表
    // 由于用例还没有保存到数据库，使用临时 ID
    return result?.testCases?.map((_, index) => `temp-${index}`) || [];
  }, [result?.testCases]);

  const showWelcome = !isGenerating && progress.stage === 'idle' && generatedCases.length === 0;

  return (
    <div className="flex flex-col h-full">
      {/* 主内容区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto">
          {/* 欢迎信息 */}
          {showWelcome && uploadedFiles.length === 0 && (
            <div className="text-center py-20">
              <h1 className="text-3xl font-bold text-gray-800 mb-4">
                测试用例生成平台
              </h1>
              <p className="text-gray-500 mb-8">
                描述你的需求，自动生成功能测试用例
              </p>
              <div className="flex justify-center gap-4 text-gray-400 text-sm">
                <span>支持 Markdown</span>
                <span>•</span>
                <span>纯文本</span>
                <span>•</span>
                <span>PDF 格式</span>
              </div>
            </div>
          )}

          {/* 文件预览列表 */}
          {uploadedFiles.length > 0 && showWelcome && (
            <div className="space-y-4 mb-4">
              {uploadedFiles.map((file) => (
                <FilePreview
                  key={file.uid}
                  filename={file.name}
                  mimeType={file.file.type}
                  size={file.size}
                  content={file.parsedContent}
                  loading={file.uploadProgress !== undefined && file.uploadProgress < 100 && !file.uploadError}
                  progress={file.uploadProgress}
                  error={file.uploadError}
                  onRemove={() => handleRemoveFile(file.uid)}
                />
              ))}
            </div>
          )}

          {/* 生成进度 */}
          {(isGenerating || progress.stage !== 'idle') && (
            <StreamingMessage
              progress={progress}
              testCases={result?.testCases}
            />
          )}

          {/* 生成完成后的操作按钮 */}
          {progress.stage === 'completed' && result?.testCases && result.testCases.length > 0 && (
            <div className="flex justify-center gap-4 mt-4">
              <Button type="primary" onClick={handleSaveCases}>
                保存用例
              </Button>
              <Button onClick={handleExportCases}>导出</Button>
              <Button onClick={reset}>重新生成</Button>
            </div>
          )}
        </div>
      </div>

      {/* 输入区域 */}
      <div className="border-t border-gray-100 p-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSend={handleSend}
            onFileUpload={handleFileUpload}
            disabled={isGenerating}
            placeholder={
              isGenerating
                ? '正在生成...'
                : '描述你想要测试的功能需求...'
            }
          />
          {isGenerating && (
            <div className="flex justify-center mt-3">
              <Button danger onClick={cancel}>
                取消生成
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 导出对话框 */}
      <ExportDialog
        open={exportDialogOpen}
        testCaseIds={getTestCaseIds()}
        onClose={() => setExportDialogOpen(false)}
      />

      {/* 保存对话框 */}
      <Modal
        title="选择需求"
        open={saveDialogOpen}
        onCancel={() => setSaveDialogOpen(false)}
        onOk={() => {
          if (selectedRequirementId) {
            // Trigger save by setting requirement ID
            handleSaveCases();
          }
        }}
        okText="保存"
      >
        <div className="p-4">
          <p className="mb-4 text-gray-600">选择要保存到的需求：</p>
          <Select
            placeholder="选择需求"
            value={selectedRequirementId}
            onChange={setSelectedRequirementId}
            style={{ width: '100%' }}
            loading={requirements === undefined}
          >
            {requirements?.map((req) => (
              <Select.Option key={req.id} value={req.id}>
                {req.title}
              </Select.Option>
            ))}
          </Select>
        </div>
      </Modal>
    </div>
  );
}
