const LiveLog = ({ logs }) => {
  return (
    <div className="bg-inverse_surface rounded-xl p-3 md:p-4 shadow-inner mt-4 overflow-hidden border border-surface_container_highest flex flex-col h-full">
      <div className="flex items-center justify-between mb-2 md:mb-3 border-b border-surface_variant/20 pb-2 flex-none">
        <div className="flex gap-1.5 md:gap-2">
          <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-error"></div>
          <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-tertiary"></div>
          <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-primary_container"></div>
        </div>
        <span className="text-[10px] md:text-xs text-inverse_on_surface/60 font-mono">live_output.log</span>
      </div>
      <div className="flex-1 overflow-y-auto font-mono text-[11px] md:text-sm space-y-0.5 md:space-y-1 scrollbar-thin scrollbar-thumb-surface_variant">
        {logs && logs.length > 0 ? (
          logs.map((log, idx) => (
            <div key={idx} className="flex gap-3">
              <span className="text-inverse_on_surface/40 select-none">
                {String(idx + 1).padStart(3, '0')}
              </span>
              <span className={`
                ${log.includes('✓') || log.includes('✅') || log.includes('SUCCESS') ? 'text-[#a3e635]' : ''}
                ${log.includes('✗') || log.includes('Error') ? 'text-error_container' : ''}
                ${log.includes('⚠') || log.includes('Warning') ? 'text-[#fde047]' : ''}
                ${!log.includes('✓') && !log.includes('✗') && !log.includes('⚠') && !log.includes('✅') ? 'text-inverse_on_surface' : ''}
              `}>
                {log}
              </span>
            </div>
          ))
        ) : (
          <div className="flex items-center justify-center h-full text-inverse_on_surface/40 italic">
            Waiting for execution to start...
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveLog;
