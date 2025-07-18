import axios from 'axios';
import { API_CONFIG } from '../config/api';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for error handling
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// Health check
export const checkHealth = async () => {
  const response = await apiClient.get('/health', { timeout: 5000 });
  return response.data;
};

// PDF Upload
export const uploadPDFs = async (files: File[]) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await apiClient.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Query papers
export const queryPapers = async (query: string) => {
  const formData = new FormData();
  formData.append('query', query);

  const response = await apiClient.post('/api/query', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Get available papers
export const getPapers = async () => {
  const response = await apiClient.get('/api/papers');
  return response.data;
};

// Get references
export const getReferences = async () => {
  const response = await apiClient.get('/api/references');
  return response.data;
};

// Get reference statistics
export const getReferenceStats = async () => {
  const response = await apiClient.get('/api/references/stats');
  return response.data;
};

// Extract references from PDF
export const extractReferencesFromPDF = async (pdfFilename: string) => {
  const formData = new FormData();
  formData.append('pdf_filename', pdfFilename);

  const response = await apiClient.post('/api/references/extract', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Download references
export const downloadReferences = async (referenceIds: string[]) => {
  const formData = new FormData();
  referenceIds.forEach((id) => {
    formData.append('reference_ids', id);
  });

  const response = await apiClient.post('/api/references/download', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Add manual reference
export const addManualReference = async (reference: {
  authors: string;
  title: string;
  journal: string;
  year: string;
  doi?: string;
}) => {
  const formData = new FormData();
  formData.append('authors', reference.authors);
  formData.append('title', reference.title);
  formData.append('journal', reference.journal);
  formData.append('year', reference.year);
  if (reference.doi) {
    formData.append('doi', reference.doi);
  }

  const response = await apiClient.post('/api/references/manual', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Run evaluation
export const runEvaluation = async () => {
  const response = await apiClient.post('/api/evaluate');
  return response.data;
};

export default apiClient; 