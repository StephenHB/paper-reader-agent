// API Configuration for Paper Reader Agent Frontend

export const API_CONFIG = {
  // Backend API base URL
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  
  // WebSocket URL for real-time updates
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  
  // API endpoints
  ENDPOINTS: {
    // Core endpoints
    HEALTH: '/health',
    ROOT: '/',
    
    // PDF management
    UPLOAD: '/api/upload',
    BUILD_KB: '/api/build-kb',
    
    // Query interface
    QUERY: '/api/query',
    
    // Reference management
    REFERENCES_EXTRACT: '/api/references/extract',
    REFERENCES_DOWNLOAD: '/api/references/download',
    REFERENCES_LIST: '/api/references/list',
    REFERENCES_CUSTOM: '/api/references/custom',
    
    // Evaluation
    EVALUATION: '/api/evaluation',
    SYSTEM_STATUS: '/api/system/status',
    CLEANUP: '/api/system/cleanup',
  },
  
  // Request configuration
  REQUEST_CONFIG: {
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  },
  
  // WebSocket configuration
  WS_CONFIG: {
    reconnectInterval: 1000,
    maxReconnectAttempts: 5,
  },
  
  // File upload configuration
  UPLOAD_CONFIG: {
    maxFileSize: 50 * 1024 * 1024, // 50MB
    allowedTypes: ['application/pdf'],
    maxFiles: 10,
  },
};

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Helper function to get WebSocket URL
export const getWsUrl = (): string => {
  return API_CONFIG.WS_URL;
}; 