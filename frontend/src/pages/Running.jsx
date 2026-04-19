import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Play, CheckCircle, AlertCircle, ArrowLeft, Loader2, FileText, Square } from 'lucide-react';
import LiveLog from '../components/LiveLog';
import { triggerRun, stopRun, API_BASE_URL } from '../api';

const Running = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [logs, setLogs] = useState(["[00:00:00] Initializing execution session..."]);
  const [isRunning, setIsRunning] = useState(true);
  const [isStopping, setIsStopping] = useState(false);
  const [error, setError] = useState(null);
  const [runId, setRunId] = useState(null);
  const eventSourceRef = useRef(null);
  const executionStarted = useRef(false);

  // Extract data from location state
  const { enrollment, password, file, fileId } = location.state || {};

  useEffect(() => {
    // Resume Mode: if we have a runId but no enrollment, we just view the logs
    const resumeMode = location.state?.runId && !enrollment;

    if (!resumeMode && (!enrollment || (!password && !fileId))) {
      navigate('/setup');
      return;
    }

    if (!executionStarted.current) {
      if (resumeMode) {
        resumeExecution(location.state.runId);
      } else {
        startExecution();
      }
      executionStarted.current = true;
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [enrollment, password, fileId, navigate]);

  const startExecution = async () => {
    try {
      const formData = new FormData();
      formData.append('username', enrollment);
      if (password) formData.append('password', password);
      
      if (file) {
        formData.append('file', file);
      } else if (fileId) {
        formData.append('file_id', fileId.toString());
      }

      // Use the centralized triggerRun helper (handles Auth headers)
      const res = await triggerRun(formData);
      const newRunId = res.data.run_id;
      setRunId(newRunId);

      // Start log stream
      setupEventSource(newRunId);

    } catch (err) {
      console.error("Execution error:", err);
      setError(err.message);
      setIsRunning(false);
      setLogs(prev => [...prev, `✗ Error starting execution: ${err.response?.data?.detail || err.message}`]);
    }
  };

  const resumeExecution = async (existingRunId) => {
    setRunId(existingRunId);
    // Optionally fetch run details if we want to show who the run is for
    try {
      const { getRunDetail } = await import('../api');
      const res = await getRunDetail(existingRunId);
      // We don't have enrollment in state, but we can display it if we want
      // For now, just connect to stream
      setupEventSource(existingRunId);
    } catch (err) {
      console.error("Failed to resume:", err);
      setIsRunning(false);
    }
  };

  const setupEventSource = (id) => {
    const token = localStorage.getItem('token');
    const sseUrl = `${API_BASE_URL}/api/run/stream?run_id=${id}${token ? `&token=${token}` : ''}`;
    
    const eventSource = new EventSource(sseUrl);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      setLogs((prev) => [...prev, event.data]);
      if (event.data.includes("SUCCESS") || event.data.includes("terminated")) {
         setIsRunning(false);
      }
    };

    eventSource.addEventListener('done', () => {
      setLogs(prev => [...prev, "✅ Execution completed successfully."]);
      setIsRunning(false);
      eventSource.close();
      
      // Auto-redirect to status page after 5 seconds of success
      setTimeout(() => {
        if (!error) {
          navigate('/status');
        }
      }, 5000);
    });

    eventSource.onerror = (e) => {
      if (eventSource.readyState === EventSource.CLOSED) return;
      setLogs(prev => [...prev, "✗ Error: Log stream disconnected."]);
      setIsRunning(false);
      eventSource.close();
    };
  };

  const handleStop = async () => {
    if (!runId || isStopping) return;
    
    setIsStopping(true);
    setLogs(prev => [...prev, "⚠️ Requesting termination..."]);
    
    try {
      await stopRun(runId);
      setLogs(prev => [...prev, "🛑 Stop signal sent. Execution will terminate shortly."]);
    } catch (err) {
      console.error("Stop error:", err);
      setLogs(prev => [...prev, `✗ Failed to stop: ${err.response?.data?.detail || err.message}`]);
      setIsStopping(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 px-4">
      <div className="flex items-center justify-between">
        <Link to="/setup" className="flex items-center gap-2 text-sm text-on_surface_variant hover:text-primary transition-colors group">
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          Back to Setup
        </Link>
        <div className="flex items-center gap-2">
           {isRunning && (
             <button
               onClick={handleStop}
               disabled={isStopping}
               className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                 isStopping 
                 ? 'bg-surface_container_highest text-on_surface_variant cursor-not-allowed' 
                 : 'bg-error text-on_error hover:bg-error/90 shadow-md shadow-error/20'
               }`}
             >
               {isStopping ? <Loader2 className="w-3 h-3 animate-spin" /> : <Square className="w-3 h-3 fill-current" />}
               {isStopping ? 'Stopping...' : 'Stop Script'}
             </button>
           )}
           <span className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 ${
             isRunning ? 'bg-primary/10 text-primary animate-pulse' : 'bg-success/10 text-success'
           }`}>
             {isRunning ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3" />}
             {isRunning ? 'Run in Progress' : 'Execution Finished'}
           </span>
        </div>
      </div>

      <header className="space-y-2">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-on_surface flex items-center gap-3">
          <div className={`p-2 rounded-xl transition-colors ${isRunning ? 'bg-primary/10' : 'bg-success/10'}`}>
            <Play className={`w-5 h-5 md:w-6 md:h-6 ${isRunning ? 'text-primary fill-primary/20' : 'text-success fill-success/20'}`} />
          </div>
          {isRunning ? 'Active Execution' : 'Execution Summary'}
        </h1>
        <p className="text-on_surface_variant">
          Uploading assignment for <span className="text-primary font-medium">{enrollment}</span>
        </p>
      </header>

      <div className="bg-surface_container p-4 md:p-6 rounded-3xl ghost-border overflow-hidden flex flex-col h-[50vh] md:h-[600px] min-h-[400px]">
        <div className="flex items-center gap-2 mb-3 md:mb-4">
           <FileText className="w-3.5 h-3.5 md:w-4 md:h-4 text-primary" />
           <h3 className="text-xs md:text-sm font-semibold uppercase tracking-wider text-on_surface_variant">Live Execution Logs</h3>
        </div>
        <div className="flex-1 overflow-hidden">
          <LiveLog logs={logs} />
        </div>
      </div>

      {!isRunning && (
        <div className="flex flex-col sm:flex-row gap-4 animate-in fade-in zoom-in duration-500">
          <button 
            onClick={() => navigate('/status')}
            className="flex-1 bg-primary text-on_primary py-4 rounded-2xl font-semibold hover:shadow-lg hover:shadow-primary/20 transition-all flex items-center justify-center gap-2"
          >
            <CheckCircle className="w-5 h-5" /> View History
          </button>
          <button 
            onClick={() => navigate('/setup')}
            className="flex-1 bg-surface_container_highest text-on_surface py-4 rounded-2xl font-semibold hover:bg-surface_container_high transition-all flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-5 h-5" /> Run Another
          </button>
        </div>
      )}
    </div>
  );
};

export default Running;
