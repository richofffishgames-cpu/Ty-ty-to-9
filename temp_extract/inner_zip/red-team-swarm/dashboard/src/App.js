import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Box,
  LinearProgress
} from '@mui/material';
import {
  Security,
  BugReport,
  CheckCircle,
  Warning,
  Error,
  PlayArrow,
  Stop,
  Visibility
} from '@mui/icons-material';
import { collection, onSnapshot, query, orderBy, limit, addDoc } from 'firebase/firestore';
import { db } from './firebase-config';
import './App.css';

function App() {
  const [workflows, setWorkflows] = useState([]);
  const [scans, setScans] = useState([]);
  const [validations, setValidations] = useState([]);
  const [exploitations, setExploitations] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startDialogOpen, setStartDialogOpen] = useState(false);
  const [target, setTarget] = useState('');
  const [scanType, setScanType] = useState('basic');

  useEffect(() => {
    // Real-time listeners for all collections
    const unsubscribeWorkflows = onSnapshot(
      query(collection(db, 'workflow_executions'), orderBy('start_time', 'desc'), limit(10)),
      (snapshot) => {
        setWorkflows(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      }
    );

    const unsubscribeScans = onSnapshot(
      query(collection(db, 'scans'), orderBy('timestamp', 'desc'), limit(20)),
      (snapshot) => {
        setScans(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      }
    );

    const unsubscribeValidations = onSnapshot(
      query(collection(db, 'validations'), orderBy('timestamp', 'desc'), limit(20)),
      (snapshot) => {
        setValidations(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      }
    );

    const unsubscribeExploitations = onSnapshot(
      query(collection(db, 'exploitations'), orderBy('timestamp', 'desc'), limit(20)),
      (snapshot) => {
        setExploitations(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      }
    );

    setLoading(false);

    return () => {
      unsubscribeWorkflows();
      unsubscribeScans();
      unsubscribeValidations();
      unsubscribeExploitations();
    };
  }, []);

  const handleStartEngagement = async () => {
    if (!target) return;

    try {
      // Trigger workflow execution via API call
      const response = await fetch('/api/start-workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target: target,
          scan_type: scanType
        })
      });

      if (response.ok) {
        setStartDialogOpen(false);
        setTarget('');
        // Show success notification
      }
    } catch (error) {
      console.error('Failed to start engagement:', error);
    }
  };

  const handleDecision = async (decisionType, workflowId) => {
    try {
      await addDoc(collection(db, 'human_decisions'), {
        workflow_id: workflowId,
        decision: decisionType,
        timestamp: new Date(),
        operator: 'current_user' // In real app, get from auth
      });
    } catch (error) {
      console.error('Failed to submit decision:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'initiated': return 'info';
      case 'foothold_achieved': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
        <Typography variant="h6" align="center" sx={{ mt: 2 }}>
          Loading Red Team Dashboard...
        </Typography>
      </Box>
    );
  }

  return (
    <div className="App">
      <AppBar position="static" sx={{ bgcolor: '#1a1a1a' }}>
        <Toolbar>
          <Security sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Red Team Agent Swarm Dashboard
          </Typography>
          <Button
            color="inherit"
            startIcon={<PlayArrow />}
            onClick={() => setStartDialogOpen(true)}
          >
            Start Engagement
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Grid container spacing={3}>
          {/* Status Overview */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Active Workflows
                </Typography>
                <List>
                  {workflows.map((workflow) => (
                    <ListItem key={workflow.id}>
                      <ListItemIcon>
                        {workflow.status === 'foothold_achieved' ?
                          <Warning color="warning" /> :
                          <CheckCircle color="success" />
                        }
                      </ListItemIcon>
                      <ListItemText
                        primary={`Target: ${workflow.target}`}
                        secondary={`Status: ${workflow.status} | Started: ${workflow.start_time?.toDate?.()?.toLocaleString() || 'Unknown'}`}
                      />
                      <Chip
                        label={workflow.status}
                        color={getStatusColor(workflow.status)}
                        size="small"
                      />
                      {workflow.status === 'foothold_achieved' && (
                        <Box sx={{ ml: 2 }}>
                          <Button
                            size="small"
                            variant="outlined"
                            color="primary"
                            onClick={() => handleDecision('continue_lateral_movement', workflow.id)}
                            sx={{ mr: 1 }}
                          >
                            Continue
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="secondary"
                            onClick={() => handleDecision('gather_intelligence', workflow.id)}
                            sx={{ mr: 1 }}
                          >
                            Gather Intel
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            onClick={() => handleDecision('stop_engagement', workflow.id)}
                          >
                            Stop
                          </Button>
                        </Box>
                      )}
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Stats */}
          <Grid item xs={12} md={4}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Statistics
                    </Typography>
                    <Typography variant="body2">
                      Active Scans: {scans.filter(s => s.status === 'running').length}
                    </Typography>
                    <Typography variant="body2">
                      Validated Targets: {validations.filter(v => v.validation_result?.is_vulnerable).length}
                    </Typography>
                    <Typography variant="body2">
                      Successful Exploits: {exploitations.filter(e => e.exploit_result?.success).length}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>

          {/* Recent Scans */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Scans
                </Typography>
                <List dense>
                  {scans.slice(0, 5).map((scan) => (
                    <ListItem key={scan.id}>
                      <ListItemIcon>
                        <Visibility />
                      </ListItemIcon>
                      <ListItemText
                        primary={scan.target}
                        secondary={`${scan.hypotheses_count || 0} hypotheses | ${scan.scan_type}`}
                      />
                      <Chip
                        label={scan.status}
                        color={getStatusColor(scan.status)}
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Validations */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Validations
                </Typography>
                <List dense>
                  {validations.slice(0, 5).map((validation) => (
                    <ListItem key={validation.id}>
                      <ListItemIcon>
                        {validation.validation_result?.is_vulnerable ?
                          <BugReport color="error" /> :
                          <CheckCircle color="success" />
                        }
                      </ListItemIcon>
                      <ListItemText
                        primary={`${validation.target}:${validation.port}`}
                        secondary={`${validation.service} | ${validation.validation_result?.vulnerability || 'Clean'}`}
                      />
                      {validation.validation_result?.is_vulnerable && (
                        <Chip
                          label={validation.validation_result.severity}
                          color={getSeverityColor(validation.validation_result.severity)}
                          size="small"
                        />
                      )}
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Exploitations */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Exploitation Attempts
                </Typography>
                <List>
                  {exploitations.slice(0, 10).map((exploit) => (
                    <ListItem key={exploit.id}>
                      <ListItemIcon>
                        {exploit.exploit_result?.success ?
                          <Error color="error" /> :
                          <CheckCircle color="success" />
                        }
                      </ListItemIcon>
                      <ListItemText
                        primary={`${exploit.target}:${exploit.port} (${exploit.service})`}
                        secondary={
                          exploit.exploit_result?.success ?
                          `SUCCESS: ${exploit.exploit_result.access_level} | ${exploit.exploit_result.payload_type}` :
                          `FAILED: ${exploit.exploit_result?.error || 'No vulnerability confirmed'}`
                        }
                      />
                      <Chip
                        label={exploit.exploit_result?.success ? 'Compromised' : 'Safe'}
                        color={exploit.exploit_result?.success ? 'error' : 'success'}
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Start Engagement Dialog */}
      <Dialog open={startDialogOpen} onClose={() => setStartDialogOpen(false)}>
        <DialogTitle>Start New Red Team Engagement</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Ensure you have explicit authorization before proceeding.
          </Alert>
          <TextField
            autoFocus
            margin="dense"
            label="Target (IP/Domain)"
            fullWidth
            variant="outlined"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            select
            margin="dense"
            label="Scan Type"
            fullWidth
            variant="outlined"
            value={scanType}
            onChange={(e) => setScanType(e.target.value)}
            SelectProps={{
              native: true,
            }}
          >
            <option value="basic">Basic Scan</option>
            <option value="comprehensive">Comprehensive Scan</option>
            <option value="stealth">Stealth Scan</option>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStartDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleStartEngagement}
            variant="contained"
            color="primary"
            disabled={!target}
          >
            Start Engagement
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default App;
