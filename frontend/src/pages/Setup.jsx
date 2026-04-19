import { useState, useRef, useEffect } from 'react';
import { Eye, EyeOff, Play, Save, Settings, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import FileDropZone from '../components/FileDropZone';
import LiveLog from '../components/LiveLog';
import { triggerRun, saveConfig, getConfig, enableSchedule as apiEnableSchedule, disableSchedule, API_BASE_URL } from '../api';

const Setup = () => {
  const navigate = useNavigate();
  // Form State
  const [enrollment, setEnrollment] = useState('');
  const [password, setPassword] = useState('');
  const [file, setFile] = useState(null);
  
  // Schedule State
  const [scheduleTime, setScheduleTime] = useState('08:00');
  const [isScheduleEnabled, setIsScheduleEnabled] = useState(false);
  const [savedFileId, setSavedFileId] = useState(null);
  const [savedFileName, setSavedFileName] = useState('');

  // UI State
  const [showPassword, setShowPassword] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');
  const [formIntent, setFormIntent] = useState(null); // 'run' or 'save'
  
  // EventSource ref for cleanup
  const sseRef = useRef(null);

  // Cleanup SSE on unmount
  useEffect(() => {
    // Load saved config on mount
    const loadConfig = async () => {
      try {
        const res = await getConfig();
        if (res.data.username) setEnrollment(res.data.username);
        if (res.data.schedule_time) setScheduleTime(res.data.schedule_time);
        if (res.data.schedule_enabled !== undefined) setIsScheduleEnabled(res.data.schedule_enabled);
        if (res.data.file_id) setSavedFileId(res.data.file_id);
        if (res.data.file_name) setSavedFileName(res.data.file_name);
      } catch (err) {
        console.error("Failed to load saved config:", err);
      }
    };
    loadConfig();

    return () => {
      if (sseRef.current) {
        sseRef.current.close();
      }
    };
  }, []);

  const handleRunNow = () => {
    const hasSavedConfig = savedFileId !== null;
    if (!enrollment || (!password && !hasSavedConfig) || (!file && !savedFileId)) {
      setErrorMsg("Please fill in enrollment, password, and attach a file to run.");
      return;
    }
    
    // Navigate to the dedicated running page with form data
    // This "real" navigation is critical for Chrome to trigger the password save prompt.
    navigate('/running', { 
      state: { 
        enrollment, 
        password, 
        file, 
        fileId: savedFileId 
      } 
    });
  };

  const handleSaveConfig = async () => {
    const hasSavedConfig = savedFileId !== null;
    if (!enrollment || (!password && !hasSavedConfig) || (!file && !savedFileId)) {
      setErrorMsg("Please fill in all fields (including the file) to save config.");
      return;
    }
    
    setErrorMsg('');
    try {
      const formData = new FormData();
      formData.append('username', enrollment);
      formData.append('password', password);
      if (file) {
        formData.append('file', file);
      } else if (savedFileId) {
        formData.append('file_id', savedFileId.toString());
      }
      formData.append('schedule_time', scheduleTime);
      formData.append('schedule_enabled', isScheduleEnabled ? 'true' : 'false');
      
      await saveConfig(formData);

      alert("Configuration and Schedule saved successfully!");
      navigate('/status');
    } catch (err) {
      setErrorMsg("Failed to save configuration.");
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (formIntent === 'run') {
      handleRunNow();
    } else if (formIntent === 'save') {
      handleSaveConfig();
    }
  };

  return (
    <form 
      onSubmit={handleFormSubmit} 
      method="POST"
      action="#"
      className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-2xl mx-auto"
    >
      <div className="mb-6 md:mb-8">
        <h2 className="text-2xl md:text-3xl font-display font-semibold text-on_surface mb-2">Automate Your Uploads</h2>
        <p className="text-sm md:text-base text-on_surface_variant leading-relaxed">Configure your credentials, upload the assignment file, and let the system handle the repetition.</p>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-error_container text-on_error_container flex items-start gap-3 shadow-sm border border-error/20">
           <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
           <p className="font-medium text-sm">{errorMsg}</p>
        </div>
      )}

      <div className="bg-surface_container_lowest rounded-2xl p-5 md:p-8 shadow-sm border border-surface_container_highest mb-6">
        <h3 className="text-sm font-semibold mb-4 text-on_surface flex items-center gap-2">
          <Settings className="w-4 h-4 text-primary" />
          Credentials
        </h3>
        
        <div className="space-y-4">
          {isRunning ? (
            <div className="py-2 animate-in fade-in duration-500">
               <p className="text-sm font-medium text-on_surface_variant">Script is currently executing for:</p>
               <p className="text-lg font-bold text-primary">{enrollment}</p>
               <p className="text-xs text-on_surface_variant/60 mt-1 italic">Input locked during execution to ensure consistency.</p>
            </div>
          ) : (
            <>
              <div>
                <label htmlFor="enrollment" className="block text-xs font-medium text-on_surface_variant mb-1 uppercase tracking-wider">Enrollment Number</label>
                <input 
                  id="enrollment"
                  type="text" 
                  name="username"
                  autoComplete="username"
                  value={enrollment}
                  onChange={(e) => setEnrollment(e.target.value)}
                  placeholder="e.g. 0832CSxxxx"
                  className="w-full bg-surface_container_highest border-none text-on_surface rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary/40 ghost-border outline-none transition-shadow"
                />
              </div>
              
              <div className="relative">
                <label htmlFor="password" className="block text-xs font-medium text-on_surface_variant mb-1 uppercase tracking-wider">Password</label>
                <input 
                  id="password"
                  type={showPassword ? 'text' : 'password'} 
                  name="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={savedFileId ? "•••••••• (Saved)" : "Portal Password"}
                  className="w-full bg-surface_container_highest border-none text-on_surface rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary/40 ghost-border outline-none transition-shadow pr-10"
                />
                <button 
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-8 text-on_surface_variant hover:text-primary transition-colors focus:outline-none"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="bg-surface_container_lowest rounded-2xl p-5 md:p-8 shadow-sm border border-surface_container_highest mb-6 flex flex-col md:flex-row gap-6 md:gap-8">
        <div className="flex-1">
          <FileDropZone onFileSelect={setFile} />
          {savedFileName && !file && (
            <p className="text-xs text-primary mt-3 flex items-center gap-1 font-medium bg-primary/5 p-2 rounded-lg border border-primary/10">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
              Using saved file: <span className="underline italic">{savedFileName}</span>
            </p>
          )}
        </div>
        
        <div className="w-px bg-surface_variant hidden md:block"></div>
        <hr className="bg-surface_variant h-px border-none md:hidden" />
        
        <div className="flex-1">
          <h3 className="text-sm font-semibold mb-4 text-on_surface flex items-center gap-2">
            Schedule (Optional)
          </h3>
          <div className="space-y-4">
             <div>
               <label className="block text-xs font-medium text-on_surface_variant mb-1 uppercase tracking-wider">Run daily at</label>
               <input 
                 type="time" 
                 value={scheduleTime}
                 onChange={(e) => setScheduleTime(e.target.value)}
                 className="w-full bg-surface_container_highest border-none text-on_surface rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-primary/40 ghost-border outline-none transition-shadow"
               />
             </div>
             <label className="flex items-center gap-3 cursor-pointer group mt-4">
               <div className="relative flex items-center justify-center">
                 <input 
                   type="checkbox" 
                   checked={isScheduleEnabled}
                   onChange={(e) => setIsScheduleEnabled(e.target.checked)}
                   className="peer sr-only" 
                 />
                 <div className="w-5 h-5 border-2 border-outline_variant rounded bg-surface_container_highest peer-checked:bg-primary peer-checked:border-primary transition-all"></div>
                 <svg className="absolute w-3 h-3 text-on_primary opacity-0 peer-checked:opacity-100 fill-current" viewBox="0 0 20 20">
                   <path d="M0 11l2-2 5 5L18 3l2 2L7 18z"/>
                 </svg>
               </div>
               <span className="text-sm font-medium text-on_surface group-hover:text-primary transition-colors">Enable daily auto-run</span>
             </label>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-4">
        <button 
          type="submit"
          onClick={() => setFormIntent('run')}
          disabled={isRunning}
          className="w-full sm:w-auto px-8 py-3 rounded-lg font-semibold text-sm transition-all shadow-md flex items-center justify-center gap-2 bg-gradient-to-r from-primary to-primary_container text-on_primary hover:shadow-lg hover:scale-[1.02] disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isRunning ? (
            <div className="w-4 h-4 border-2 border-on_primary border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <Play className="w-4 h-4 fill-current" />
          )}
          {isRunning ? 'Running Script...' : 'Run Now'}
        </button>
        
        <button 
          type="submit"
          onClick={() => setFormIntent('save')}
          className="w-full sm:w-auto px-8 py-3 rounded-lg font-semibold text-sm transition-all bg-surface_container_high text-primary hover:bg-surface_container_highest shadow-sm flex items-center justify-center gap-2"
        >
          <Save className="w-4 h-4" />
          Save & Schedule
        </button>
      </div>
      
      <p className="text-xs text-on_surface_variant mt-4 flex items-center gap-2">
        <span className="text-tertiary">⚠</span> 
        Credentials are stored securely encrypted on the server.
      </p>


      {/* File History Section */}
      <FileHistorySection />
    </form>
  );
};

const FileHistorySection = () => {
  const [files, setFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchFiles = async () => {
    setIsLoading(true);
    try {
      const res = await import('../api').then(m => m.getFiles());
      setFiles(res.data);
    } catch (err) {
      console.error("Failed to fetch files:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this file from the history?")) return;
    try {
      await import('../api').then(m => m.deleteFile(id));
      fetchFiles();
    } catch (err) {
      alert("Failed to delete file.");
    }
  };

  if (files.length === 0 && !isLoading) return null;

  return (
    <div className="mt-12 animate-in fade-in slide-in-from-top-4 duration-700">
      <div className="flex items-center gap-3 mb-6">
        <div className="h-px bg-surface_variant flex-1"></div>
        <h3 className="text-xs font-bold uppercase tracking-widest text-on_surface_variant">Past Uploads History</h3>
        <div className="h-px bg-surface_variant flex-1"></div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {files.map(f => (
          <div key={f.id} className="bg-surface_container_highest/30 rounded-xl p-4 border border-surface_container_highest/50 flex justify-between items-center group hover:bg-surface_container_highest/50 transition-all">
            <div className="overflow-hidden">
              <p className="text-sm font-medium text-on_surface truncate" title={f.original_name}>{f.original_name}</p>
              <p className="text-[10px] text-on_surface_variant mt-0.5 uppercase tracking-tight">
                {f.file_size_kb} KB • {new Date(f.uploaded_at).toLocaleDateString()}
              </p>
            </div>
            <button 
              onClick={() => handleDelete(f.id)}
              className="p-2 text-on_surface_variant hover:text-error hover:bg-error/10 rounded-lg transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
              title="Delete from history"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Setup;
