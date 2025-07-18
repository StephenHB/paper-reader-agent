# Paper Reader Agent - React Frontend

## Overview

This is the modern React frontend for the Paper Reader Agent web application. It provides a responsive, user-friendly interface for all Paper Reader Agent functionality with real-time progress tracking.

## Features

- **Modern UI**: Built with React 18, TypeScript, and Material-UI
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: WebSocket integration for live progress tracking
- **Drag & Drop**: Intuitive file upload interface
- **Reference Management**: Complete reference extraction and download interface
- **Query Interface**: Natural language querying with source attribution
- **Evaluation System**: Integration with existing evaluation framework

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Material-UI (MUI)** for modern UI components
- **React Router** for navigation
- **Axios** for API communication
- **WebSocket** for real-time updates

## Setup

### Prerequisites

1. Node.js 16+ installed
2. Backend API running (see web_UI/README.md)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at:
- **Development**: http://localhost:5173
- **Production Build**: `npm run build`

## Project Structure

```
UI/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout/         # Layout and navigation
│   │   ├── PDFUpload/      # PDF upload components
│   │   ├── References/     # Reference management
│   │   ├── Query/          # Query interface
│   │   ├── Evaluation/     # Evaluation system
│   │   └── common/         # Common UI components
│   ├── pages/              # Main application pages
│   ├── services/           # API integration services
│   ├── hooks/              # Custom React hooks
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   └── App.tsx             # Main application component
├── public/                 # Static assets
├── package.json            # Dependencies and scripts
└── vite.config.ts          # Vite configuration
```

## Key Components

### Layout Components
- **App**: Main application with routing
- **Layout**: Navigation and page structure
- **Sidebar**: Configuration and navigation

### PDF Upload
- **DragDropUpload**: Drag-and-drop file upload
- **FilePreview**: File preview and management
- **UploadProgress**: Real-time upload progress

### Reference Management
- **ReferenceList**: Display and select references
- **DownloadConfig**: Configure download settings
- **CustomDownload**: Manual reference download

### Query Interface
- **QueryInput**: Natural language query input
- **ResultsDisplay**: Query results with sources
- **KnowledgeBase**: Knowledge base management

### Evaluation
- **EvaluationPanel**: Evaluation metrics display
- **SystemMonitor**: System performance monitoring
- **CleanupPanel**: File cleanup operations

## API Integration

The frontend communicates with the FastAPI backend through:

- **REST APIs**: For data operations (upload, query, etc.)
- **WebSocket**: For real-time progress updates
- **File Upload**: Multipart form data for PDF uploads

## Development

### Adding New Components

1. Create component in appropriate directory under `src/components/`
2. Use TypeScript interfaces for props
3. Follow Material-UI design patterns
4. Add proper error handling and loading states

### State Management

- **Context API**: For global state (user settings, app state)
- **Local State**: For component-specific state
- **Custom Hooks**: For reusable state logic

### Styling

- **Material-UI**: Primary styling framework
- **CSS Modules**: For component-specific styles
- **Responsive Design**: Mobile-first approach

## Configuration

The frontend connects to the backend API at:
- **Development**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws

Configuration can be modified in `src/config/api.ts`.

## Building for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- **Code Splitting**: Automatic route-based code splitting
- **Lazy Loading**: Components loaded on demand
- **Optimized Bundles**: Vite optimizations for fast loading
- **Caching**: Efficient caching strategies

## Accessibility

- **ARIA Labels**: Proper accessibility attributes
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: Compatible with screen readers
- **Color Contrast**: WCAG compliant color schemes
