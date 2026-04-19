import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import LiveLog from './LiveLog';
import { getRunDetail } from '../api';

const RunHistory = ({ historyData }) => {
  const [expandedId, setExpandedId] = useState(null);
  const [runLogs, setRunLogs] = useState({}); // { [runId]: logs[] }
  const [loadingIds, setLoadingIds] = useState(new Set());

  const handleToggle = async (runId, index) => {
    if (expandedId === index) {
      setExpandedId(null);
      return;
    }

    setExpandedId(index);

    // If logs aren't loaded yet, fetch them
    if (runId && !runLogs[runId] && !loadingIds.has(runId)) {
      setLoadingIds(prev => new Set(prev).add(runId));
      try {
        const res = await getRunDetail(runId);
        const fullLogs = res.data.log_text ? res.data.log_text.split('\n') : [];
        setRunLogs(prev => ({ ...prev, [runId]: fullLogs }));
      } catch (err) {
        console.error("Failed to fetch run logs:", err);
        setRunLogs(prev => ({ ...prev, [runId]: ["✗ Error: Failed to load logs from server."] }));
      } finally {
        setLoadingIds(prev => {
          const next = new Set(prev);
          next.delete(runId);
          return next;
        });
      }
    }
  };

  if (!historyData || historyData.length === 0) {
    return (
      <div className="bg-surface_container_lowest rounded-2xl shadow-sm border border-surface_container_highest p-6 text-center text-on_surface_variant">
         No run history available yet.
      </div>
    );
  }

  return (
    <div className="bg-surface_container_lowest rounded-2xl shadow-sm border border-surface_container_highest overflow-hidden">
      <div className="p-6 border-b border-surface_container_highest">
        <h3 className="text-lg font-display font-semibold text-on_surface">Run History</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-surface_container text-xs uppercase font-semibold text-on_surface_variant">
              <tr>
                <th className="px-3 md:px-6 py-4 rounded-tl-xl text-xs">Date/Time</th>
                <th className="hidden sm:table-cell px-6 py-4 text-xs">Triggered</th>
                <th className="px-3 md:px-6 py-4 text-xs">Status</th>
                <th className="px-3 md:px-6 py-4 text-xs text-center">Uploads</th>
                <th className="px-3 md:px-6 py-4 rounded-tr-xl text-right text-xs">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface_variant whitespace-nowrap">
              {historyData.map((item, index) => (
                <React.Fragment key={index}>
                  <tr 
                    onClick={() => handleToggle(item.id, index)}
                    className={`cursor-pointer transition-colors hover:bg-surface_container_low ${
                      expandedId === index ? 'bg-surface_container_low' : ''
                    }`}
                  >
                    <td className="px-3 md:px-6 py-4 font-medium text-on_background">
                      <div className="text-[11px] md:text-sm">
                        {item.formatted_date || (item.started_at ? new Date(item.started_at).toLocaleString() : 'Pending...')}
                      </div>
                    </td>
                    <td className="hidden sm:table-cell px-6 py-4 text-on_surface_variant capitalize">
                      {item.triggered_by || 'manual'}
                    </td>
                    <td className="px-3 md:px-6 py-4">
                      {item.status?.toLowerCase() === 'running' ? (
                        <span className="inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-[10px] md:text-xs font-bold bg-primary/10 text-primary animate-pulse">
                          ⚡ RUNNING
                        </span>
                      ) : item.status?.toLowerCase() === 'success' ? (
                        <span className="inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-[10px] md:text-xs font-bold bg-[#dcfce7] text-[#166534]">
                          ✅ SUCCESS
                        </span>
                      ) : item.status?.toLowerCase() === 'stopped' ? (
                        <span className="inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-[10px] md:text-xs font-bold bg-surface_container text-on_surface_variant">
                          ⏹️ STOPPED
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 md:px-2.5 py-0.5 rounded-full text-[10px] md:text-xs font-bold bg-[#fee2e2] text-[#991b1b]">
                          ❌ FAILED
                        </span>
                      )}
                    </td>
                    <td className="px-3 md:px-6 py-4 text-center">
                      <span className="text-base md:text-lg font-display font-bold text-on_surface">
                        {item.upload_count ?? 0}
                      </span>
                    </td>
                    <td className="px-3 md:px-6 py-4 text-right">
                      {loadingIds.has(item.id) ? (
                        <Loader2 className="w-4 h-4 inline text-primary animate-spin" />
                    ) : expandedId === index ? (
                      <ChevronUp className="w-4 h-4 inline text-on_surface_variant" />
                    ) : (
                      <ChevronDown className="w-4 h-4 inline text-on_surface_variant" />
                    )}
                  </td>
                </tr>
                {expandedId === index && (
                  <tr>
                    <td colSpan="5" className="px-3 md:px-6 py-4 bg-surface_container_low animate-in slide-in-from-top-2">
                       {loadingIds.has(item.id) ? (
                         <div className="flex flex-col items-center justify-center py-8 gap-3 text-on_surface_variant italic">
                            <Loader2 className="w-6 h-6 animate-spin text-primary" />
                            <p className="text-sm">Loading run logs...</p>
                         </div>
                       ) : (
                         <LiveLog logs={runLogs[item.id] || []} />
                       )}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RunHistory;
