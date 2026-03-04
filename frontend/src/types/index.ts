export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface TestCase {
  id: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2';
  status: 'draft' | 'pending' | 'approved' | 'rejected';
  projectId: string;
  projectName: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export interface Document {
  id: string;
  name: string;
  type: string;
  uploadedAt: string;
  status: 'processing' | 'completed' | 'failed';
  projectId?: string;
}

export interface LLMConfig {
  provider: string;
  apiKey: string;
  baseUrl?: string;
  model: string;
}

export interface VectorDBConfig {
  type: 'chroma' | 'faiss' | 'pinecone';
  path?: string;
  apiKey?: string;
  environment?: string;
}

export interface GenerationRequest {
  projectId: string;
  documentIds: string[];
  llmConfig: LLMConfig;
  prompt?: string;
}

export interface GenerationResponse {
  id: string;
  status: 'processing' | 'completed' | 'failed';
  testCases?: TestCase[];
  error?: string;
}
