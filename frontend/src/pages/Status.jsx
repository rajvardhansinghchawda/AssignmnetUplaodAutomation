import { useState, useEffect } from 'react';
import { Clock, CheckCircle2, History, Settings, XCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import RunHistory from '../components/RunHistory';
import { getLastStatus, getRunHistory, getScheduleInfo, enableSchedule, disableSchedule } from '../api';

const Status = () => {
  const [lastRun, setLastRun] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [statusRes, histRes, schedRes] = await Promise.all([
        getLastStatus().catch(() => ({ data: null })),
        getRunHistory(20).catch(() => ({ data: [] })),
        getScheduleInfo().catch(() => ({ data: null }))
      ]);

      setLastRun(statusRes.data);
      setHistory(histRes.data);
      setSchedule(schedRes.data);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleToggleSchedule = async () => {
    if (!schedule) return;
    try {
      if (schedule.schedule_enabled) {
        await disableSchedule();
      } else {
        // Assume schedule.schedule_time holds the configured time string
        await enableSchedule(schedule.schedule_time || '08:00');
      }
      // Refresh the schedule data
      const schedRes = await getScheduleInfo();
      setSchedule(schedRes.data);
    } catch (err) {
      console.error("Toggle error:", err);
    }
  };

  if (isLoading) {
    return <div className="text-center mt-10 text-on_surface_variant">Loading dashboard...</div>;
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-display font-semibold text-on_surface mb-2">Status Dashboard</h2>
          <p className="text-on_surface_variant">Monitor recent uploads and your auto-run schedule.</p>
        </div>
        <Link to="/setup" className="hidden sm:flex px-4 py-2 bg-surface_container_high text-primary hover:bg-surface_container_highest rounded-lg text-sm font-medium items-center gap-2 shadow-sm transition-all">
          <Settings className="w-4 h-4" />
          Edit Config
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Last Run Card */}
        <div className="col-span-1 md:col-span-1 bg-surface_container_lowest rounded-2xl p-6 shadow-sm border border-surface_container_highest flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-on_surface_variant mb-4 flex items-center gap-2">
              <History className="w-4 h-4 text-primary" />
              Last Run
            </h3>
            {lastRun && lastRun.status ? (
              <div className="flex items-center gap-2 mb-2">
                {lastRun.status === 'SUCCESS' ? (
                   <CheckCircle2 className="w-6 h-6 text-[#16a34a] fill-[#dcfce7]" />
                 ) : (
                   <XCircle className="w-6 h-6 text-[#dc2626] fill-[#fee2e2]" />
                 )}
                <span className="text-2xl font-display font-bold text-on_background">{lastRun.status}</span>
              </div>
            ) : (
              <div className="text-on_surface_variant mb-2">No run recorded</div>
            )}
          </div>
          {lastRun && lastRun.timestamp && (
            <div className="mt-4">
               <p className="text-sm font-medium text-on_surface">{lastRun.formatted_date || lastRun.timestamp}</p>
               <p className="text-xs text-on_surface_variant mt-1">{lastRun.upload_count != null ? `${lastRun.upload_count} file(s) uploaded` : lastRun.error}</p>
            </div>
          )}
        </div>

        {/* Schedule Card */}
        <div className="col-span-1 md:col-span-2 bg-gradient-to-br from-surface_container_lowest to-surface_container rounded-2xl p-6 shadow-sm border border-surface_container_highest flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-on_surface_variant mb-2 flex items-center gap-2">
              <Clock className="w-4 h-4 text-primary" />
              Next Scheduled Run
            </h3>
            <p className="text-xl font-display font-semibold text-on_background mt-1">
               {schedule?.schedule_enabled ? `Daily at ${schedule.schedule_time}` : 'Not Scheduled'}
            </p>
            <div className="flex items-center gap-2 mt-3 text-sm">
               <span className="flex items-center gap-1.5 font-medium text-on_surface">
                 Scheduler: 
                 {schedule?.schedule_enabled ? (
                   <span className="px-2 py-0.5 rounded-full bg-[#dcfce7] text-[#166534] text-xs font-bold uppercase tracking-wider">
                     Active 🟢
                   </span>
                 ) : (
                   <span className="px-2 py-0.5 rounded-full bg-surface_variant text-on_surface_variant text-xs font-bold uppercase tracking-wider">
                     Inactive ⚪
                   </span>
                 )}
               </span>
            </div>
          </div>
          <button 
            onClick={handleToggleSchedule}
            className="px-4 py-2 text-sm font-medium rounded-lg border border-outline_variant text-on_surface hover:bg-surface_container transition-colors bg-surface_container_lowest shadow-sm">
            {schedule?.schedule_enabled ? 'Disable' : 'Enable'}
          </button>
        </div>
      </div>

      <RunHistory historyData={history} />

      <div className="mt-8 flex justify-center sm:hidden">
         <Link to="/setup" className="px-6 py-3 bg-surface_container_high text-primary hover:bg-surface_container_highest rounded-lg text-sm font-medium flex items-center gap-2 shadow-sm w-full justify-center">
            <Settings className="w-4 h-4" />
            Edit Config
         </Link>
      </div>
    </div>
  );
};

export default Status;
