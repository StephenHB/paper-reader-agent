// TypeScript type definitions for Paper Reader Agent Frontend

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// PDF File types
export interface PDFFile {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  file?: File;
}

export interface UploadedPDF {
  filename: string;
  filepath: string;
  size: number;
  uploadedAt: string;
}

// Reference types
export interface Reference {
  authors: string;
  title: string;
  journal: string;
  year: string;
  doi?: string;
  confidence: number;
}

export interface ReferenceSummary {
  total_references: number;
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
  with_doi: number;
  with_year: number;
  sample_references: Reference[];
}

// Query types
export interface QueryRequest {
  question: string;
  k?: number;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  response_time: number;
}

export interface Source {
  filename: string;
  page: number;
  chunk_index: number;
  content?: string;
}

// Knowledge Base types
export interface KnowledgeBaseStatus {
  built: boolean;
  index_name: string;
  total_chunks: number;
  total_files: number;
  last_built: string;
}

// Download Configuration types
export interface DownloadConfig {
  download_path: string;
  max_concurrent_downloads: number;
  retry_attempts: number;
  timeout_seconds: number;
  enable_arxiv: boolean;
  enable_pubmed: boolean;
  enable_google_scholar: boolean;
}

// Progress tracking types
export interface ProgressUpdate {
  type: 'upload' | 'extract' | 'download' | 'build_kb' | 'query';
  current: number;
  total: number;
  message: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  error?: string;
}

// Evaluation types
export interface EvaluationMetrics {
  retrieval_metrics: {
    recall: number;
    precision: number;
    f1_score: number;
  };
  generation_metrics: {
    semantic_similarity: number;
    bleu_score: number;
    entity_coverage: number;
  };
  system_metrics: {
    response_time: number;
    cpu_usage: number;
    memory_usage: number;
  };
}

// System status types
export interface SystemStatus {
  ollama_running: boolean;
  models_loaded: boolean;
  disk_space: number;
  memory_usage: number;
  cpu_usage: number;
}

// User consent types
export interface ConsentRecord {
  timestamp: string;
  user_id: string;
  pdf_filename: string;
  total_references: number;
  selected_references: number;
  download_path: string;
  consent_given: boolean;
  session_id: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'progress' | 'status' | 'error' | 'notification';
  data: ProgressUpdate | SystemStatus | string;
  timestamp: string;
}

// Component prop types
export interface LayoutProps {
  children: React.ReactNode;
}

export interface PDFUploadProps {
  onUploadComplete: (files: UploadedPDF[]) => void;
  onProgress: (progress: ProgressUpdate) => void;
}

export interface ReferenceListProps {
  references: Reference[];
  onSelectionChange: (selectedIndices: number[]) => void;
  selectedIndices: number[];
}

export interface QueryInputProps {
  onQuery: (query: string) => void;
  loading: boolean;
}

export interface ResultsDisplayProps {
  results: QueryResponse;
  loading: boolean;
}

// Form types
export interface CustomReferenceForm {
  authors: string;
  title: string;
  journal: string;
  year: string;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// Navigation types
export type AppRoute = 
  | '/'
  | '/upload'
  | '/references'
  | '/query'
  | '/evaluation'
  | '/settings';

export interface NavigationItem {
  path: AppRoute;
  label: string;
  icon: string;
  description: string;
} 