import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Paper,
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Upload as UploadIcon,
  Search as SearchIcon,
  Description as DescriptionIcon,
  LibraryBooks as LibraryIcon,
  Assessment as AssessmentIcon,
  Add as AddIcon
} from '@mui/icons-material';
import './App.css';
import { 
  uploadPDFs, 
  queryPapers, 
  getPapers, 
  getReferences, 
  getReferenceStats,
  extractReferencesFromPDF,
  downloadReferences, 
  addManualReference, 
  runEvaluation,
  checkHealth 
} from './services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface Paper {
  id: string;
  title: string;
  filename: string;
}

interface Reference {
  id: string;
  authors: string;
  title: string;
  journal: string;
  year: string;
  doi?: string;
  confidence?: number;
  source_pdf?: string;
  raw_text?: string;
}

interface ReferenceStats {
  total_references: number;
  extracted_references: number;
  manual_references: number;
  summary: any;
  papers_processed: number;
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [references, setReferences] = useState<Reference[]>([]);
  const [referenceStats, setReferenceStats] = useState<ReferenceStats | null>(null);
  const [isLoadingPapers, setIsLoadingPapers] = useState(false);
  const [isLoadingReferences, setIsLoadingReferences] = useState(false);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [uploadMessage, setUploadMessage] = useState('');
  const [showManualReferenceDialog, setShowManualReferenceDialog] = useState(false);
  const [manualReference, setManualReference] = useState({
    authors: '',
    title: '',
    journal: '',
    year: '',
    doi: ''
  });

  // Check backend health on component mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const result = await checkHealth();
      setBackendStatus('connected');
    } catch (error) {
      console.error('Backend health check failed:', error);
      setBackendStatus('error');
      
      // Retry after 3 seconds
      setTimeout(() => {
        checkBackendHealth();
      }, 3000);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    // Load data when switching to relevant tabs
    if (newValue === 1) {
      loadPapers();
    } else if (newValue === 2) {
      loadReferences();
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploadStatus('uploading');
    setUploadMessage('');
    
    try {
      const result = await uploadPDFs(Array.from(files));
      setUploadStatus('success');
      setUploadMessage(`Successfully processed ${result.results.filter((r: any) => r.status === 'success').length} files`);
      
      // Reload papers list
      loadPapers();
    } catch (error) {
      setUploadStatus('error');
      setUploadMessage('Error uploading files. Please try again.');
      console.error('Upload error:', error);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    
    setIsQuerying(true);
    setQueryResult('');
    
    try {
      const result = await queryPapers(query);
      
      // Handle the response format - it's an array with [answer, sources]
      if (result && result.response) {
        if (Array.isArray(result.response)) {
          const [answer, sources] = result.response;
          setQueryResult(answer || 'No answer received');
        } else {
          setQueryResult(result.response || 'No response received');
        }
      } else {
        setQueryResult('No response received from server');
      }
    } catch (error) {
      console.error('Query error:', error);
      setQueryResult(`Error querying papers: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsQuerying(false);
    }
  };

  const loadPapers = async () => {
    setIsLoadingPapers(true);
    try {
      const result = await getPapers();
      setPapers(result.papers || []);
    } catch (error) {
      console.error('Error loading papers:', error);
    } finally {
      setIsLoadingPapers(false);
    }
  };

  const loadReferences = async () => {
    setIsLoadingReferences(true);
    setIsLoadingStats(true);
    try {
      const [refsResult, statsResult] = await Promise.all([
        getReferences(),
        getReferenceStats()
      ]);
      setReferences(refsResult.references || []);
      setReferenceStats(statsResult);
    } catch (error) {
      console.error('Error loading references:', error);
    } finally {
      setIsLoadingReferences(false);
      setIsLoadingStats(false);
    }
  };

  const handleDownloadReferences = async (referenceIds: string[]) => {
    try {
      await downloadReferences(referenceIds);
      // Show success message or update UI
    } catch (error) {
      console.error('Error downloading references:', error);
    }
  };

  const handleAddManualReference = async () => {
    try {
      await addManualReference(manualReference);
      setShowManualReferenceDialog(false);
      setManualReference({ authors: '', title: '', journal: '', year: '', doi: '' });
      loadReferences(); // Reload references
    } catch (error) {
      console.error('Error adding manual reference:', error);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      const result = await runEvaluation();
      // TODO: Show evaluation results in UI
    } catch (error) {
      console.error('Error running evaluation:', error);
    }
  };

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <LibraryIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Paper Reader Agent
          </Typography>
          <Chip 
            label={backendStatus === 'connected' ? 'Connected' : backendStatus === 'error' ? 'Disconnected' : 'Checking...'} 
            color={backendStatus === 'connected' ? 'success' : backendStatus === 'error' ? 'error' : 'default'} 
            size="small" 
            onClick={checkBackendHealth}
            sx={{ cursor: 'pointer' }}
          />
          <Button 
            size="small" 
            variant="outlined" 
            onClick={checkBackendHealth}
            sx={{ ml: 1, color: 'white', borderColor: 'white' }}
          >
            Test Connection
          </Button>
          <Chip label="v2.0.0" color="secondary" size="small" sx={{ ml: 1 }} />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="paper reader tabs">
              <Tab icon={<UploadIcon />} label="Upload Papers" />
              <Tab icon={<SearchIcon />} label="Query Papers" />
              <Tab icon={<DescriptionIcon />} label="Reference Management" />
              <Tab icon={<AssessmentIcon />} label="Evaluation" />
            </Tabs>
          </Box>

          {/* Upload Papers Tab */}
          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="h5" gutterBottom>
                  Upload Academic Papers
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  Upload PDF files to build your knowledge base. The system will extract text, 
                  create embeddings, and make papers searchable.
                </Typography>
              </Box>
              
              <Card>
                <CardContent>
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Drag and drop PDF files here
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      or click to browse files
                    </Typography>
                    <Button
                      variant="contained"
                      component="label"
                      disabled={uploadStatus === 'uploading' || backendStatus !== 'connected'}
                      startIcon={uploadStatus === 'uploading' ? <CircularProgress size={20} /> : <UploadIcon />}
                    >
                      {uploadStatus === 'uploading' ? 'Uploading...' : 'Select PDF Files'}
                      <input
                        type="file"
                        hidden
                        multiple
                        accept=".pdf"
                        onChange={handleFileUpload}
                      />
                    </Button>
                  </Box>
                  
                  {uploadMessage && (
                    <Alert severity={uploadStatus === 'success' ? 'success' : 'error'} sx={{ mt: 2 }}>
                      {uploadMessage}
                    </Alert>
                  )}
                  
                  {backendStatus !== 'connected' && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      Backend not connected. Please ensure the server is running on http://localhost:8000
                      <br />
                      <Button size="small" onClick={checkBackendHealth} sx={{ mt: 1 }}>
                        Retry Connection
                      </Button>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Box>
          </TabPanel>

          {/* Query Papers Tab */}
          <TabPanel value={tabValue} index={1}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="h5" gutterBottom>
                  Query Your Knowledge Base
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  Ask questions about your uploaded papers and get AI-powered answers with source citations.
                </Typography>
              </Box>
              
              <Card>
                <CardContent>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    variant="outlined"
                    label="Ask a question about your papers..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={isQuerying || backendStatus !== 'connected'}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleQuery}
                    disabled={!query.trim() || isQuerying || backendStatus !== 'connected'}
                    startIcon={isQuerying ? <CircularProgress size={20} /> : <SearchIcon />}
                  >
                    {isQuerying ? 'Searching...' : 'Search Papers'}
                  </Button>
                </CardContent>
              </Card>
              
              {isQuerying && (
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <CircularProgress size={24} />
                      <Typography variant="body1">
                        Searching your papers...
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              )}

              {queryResult && !isQuerying && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Search Results
                    </Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                      {queryResult}
                    </Typography>
                  </CardContent>
                </Card>
              )}

              {/* Papers List */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Available Papers ({papers.length})
                  </Typography>
                  {isLoadingPapers ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                      <CircularProgress />
                    </Box>
                  ) : papers.length > 0 ? (
                    <List>
                      {papers.map((paper) => (
                        <ListItem key={paper.id}>
                          <ListItemText 
                            primary={paper.title || paper.filename} 
                            secondary={paper.filename}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No papers available. Upload some PDFs first.
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          </TabPanel>

          {/* Reference Management Tab */}
          <TabPanel value={tabValue} index={2}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="h5" gutterBottom>
                  Reference Management
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  Manage references extracted from your papers and download related research papers.
                </Typography>
              </Box>
              
              {/* Reference Statistics */}
              {referenceStats && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Reference Statistics
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                      <Box>
                        <Typography variant="h4" color="primary">
                          {referenceStats.total_references}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total References
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="h4" color="secondary">
                          {referenceStats.extracted_references}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Extracted from PDFs
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="h4" color="success.main">
                          {referenceStats.manual_references}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Manual Entries
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="h4" color="info.main">
                          {referenceStats.papers_processed}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Papers Processed
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              )}
              
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      References ({references.length})
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={() => setShowManualReferenceDialog(true)}
                      disabled={backendStatus !== 'connected'}
                    >
                      Add Manual Reference
                    </Button>
                  </Box>
                  
                  {isLoadingReferences ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                      <CircularProgress />
                    </Box>
                  ) : references.length > 0 ? (
                    <List>
                      {references.map((reference) => (
                        <ListItem key={reference.id} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                          <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <ListItemText 
                              primary={
                                <Box>
                                  <Typography variant="subtitle1" fontWeight="bold">
                                    {reference.title}
                                  </Typography>
                                  <Typography variant="body2" color="text.secondary">
                                    {reference.authors} - {reference.journal} ({reference.year})
                                  </Typography>
                                  {reference.source_pdf && (
                                    <Chip 
                                      label={`From: ${reference.source_pdf}`} 
                                      size="small" 
                                      color="primary" 
                                      variant="outlined"
                                      sx={{ mt: 1 }}
                                    />
                                  )}
                                  {reference.confidence && (
                                    <Chip 
                                      label={`Confidence: ${Math.round(reference.confidence * 100)}%`} 
                                      size="small" 
                                      color={reference.confidence > 0.8 ? 'success' : reference.confidence > 0.6 ? 'warning' : 'error'}
                                      sx={{ ml: 1, mt: 1 }}
                                    />
                                  )}
                                </Box>
                              }
                            />
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleDownloadReferences([reference.id])}
                              disabled={backendStatus !== 'connected'}
                            >
                              Download
                            </Button>
                          </Box>
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No references found. Upload papers to extract references.
                    </Typography>
                  )}
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    disabled={references.length === 0 || backendStatus !== 'connected'}
                    onClick={() => handleDownloadReferences(references.map((r) => r.id))}
                  >
                    Download All References
                  </Button>
                </CardActions>
              </Card>
            </Box>
          </TabPanel>

          {/* Evaluation Tab */}
          <TabPanel value={tabValue} index={3}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="h5" gutterBottom>
                  System Evaluation
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  Evaluate the performance and accuracy of the Paper Reader Agent system.
                </Typography>
              </Box>
              
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Evaluation Metrics
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Run evaluations to assess retrieval accuracy, response quality, and system performance.
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    onClick={handleRunEvaluation}
                    disabled={backendStatus !== 'connected'}
                  >
                    Run Evaluation
                  </Button>
                  <Button size="small" disabled>View Results</Button>
                </CardActions>
              </Card>
            </Box>
          </TabPanel>
        </Paper>
      </Container>

      {/* Manual Reference Dialog */}
      <Dialog open={showManualReferenceDialog} onClose={() => setShowManualReferenceDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Manual Reference</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Authors"
              value={manualReference.authors}
              onChange={(e) => setManualReference({...manualReference, authors: e.target.value})}
              fullWidth
            />
            <TextField
              label="Title"
              value={manualReference.title}
              onChange={(e) => setManualReference({...manualReference, title: e.target.value})}
              fullWidth
            />
            <TextField
              label="Journal"
              value={manualReference.journal}
              onChange={(e) => setManualReference({...manualReference, journal: e.target.value})}
              fullWidth
            />
            <TextField
              label="Year"
              value={manualReference.year}
              onChange={(e) => setManualReference({...manualReference, year: e.target.value})}
              fullWidth
            />
            <TextField
              label="DOI (optional)"
              value={manualReference.doi}
              onChange={(e) => setManualReference({...manualReference, doi: e.target.value})}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowManualReferenceDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleAddManualReference}
            variant="contained"
            disabled={!manualReference.authors || !manualReference.title || !manualReference.journal || !manualReference.year}
          >
            Add Reference
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default App;
