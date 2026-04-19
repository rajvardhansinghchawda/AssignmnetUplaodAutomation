import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import LiveLog from './LiveLog';

const RunHistory = ({ historyData }) => {
  const [expandedId, setExpandedId] = useState(null);

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
              <th className="px-6 py-4 rounded-tl-xl">Date/Time</th>
              <th className="px-6 py-4">Triggered</th>
              <th className="px-6 py-4">Result</th>
              <th className="px-6 py-4">Uploads / Details</th>
              <th className="px-6 py-4 rounded-tr-xl"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface_variant whitespace-nowrap">
            {historyData.map((item, index) => (
              <React.Fragment key={index}>
                <tr 
                  onClick={() => setExpandedId(expandedId === index ? null : index)}
                  className={`cursor-pointer transition-colors hover:bg-surface_container_low ${
                    expandedId === index ? 'bg-surface_container_low' : ''
                  }`}
                >
                  {/* We map the exact properties expected from the backend GET /api/runs endpoint */}
                  <td className="px-6 py-4 font-medium text-on_background">{item.formatted_date || (item.started_at ? new Date(item.started_at).toLocaleString() : 'Pending...')}</td>
                  <td className="px-6 py-4 text-on_surface_variant capitalize">{item.triggered_by || 'manual'}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold
                      ${item.status === 'SUCCESS' ? 'bg-[#dcfce7] text-[#166534]' : 'bg-error_container text-on_error_container'}
                    `}>
                      {item.status === 'SUCCESS' ? '✅ SUCCESS' : '❌ FAILED'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-on_surface">
                    {item.status === 'SUCCESS' ? (
                      <span className="font-semibold text-primary">{item.upload_count} assignments uploaded</span>
                    ) : (
                      <span className="text-on_error_container text-xs italic">{item.error || 'Check logs for details'}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {expandedId === index ? (
                      <ChevronUp className="w-4 h-4 inline text-on_surface_variant" />
                    ) : (
                      <ChevronDown className="w-4 h-4 inline text-on_surface_variant" />
                    )}
                  </td>
                </tr>
                {expandedId === index && item.log_output && (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 bg-surface_container_low animate-in slide-in-from-top-2">
                       {/* log_output is likely a very long string from the backend, split into lines */}
                       <LiveLog logs={typeof item.log_output === 'string' ? item.log_output.split('\n') : item.log_output} />
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
