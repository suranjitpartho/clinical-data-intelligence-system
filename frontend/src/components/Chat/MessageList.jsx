import { Database, Search, Brain, AlertCircle, Download } from 'lucide-react';
import { renderMarkdown } from '../../utils/markdown-renderer';
import DataTable from './DataTable';

const MessageList = ({ messages, isLoading, scrollRef, isTraceOpen, setIsTraceOpen, traceLogs, setTraceLogs, onExport }) => {
  return (
    <div className="flex-1 w-full overflow-y-auto" ref={scrollRef}>
      <div className="max-w-3xl mx-auto w-full p-4 space-y-5 pb-6">
        
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center pt-32 pb-16 space-y-6 animate-fade-in">
            <div className="relative">
              <div className="absolute inset-0 bg-clinical-blue/20 blur-3xl rounded-full"></div>
              <h2 className="text-4xl font-display font-semibold text-white tracking-tight relative z-10">
                How can I <span className="text-clinical-blue">assist</span> you today?
              </h2>
            </div>
            <p className="text-gray-400 text-center max-w-md text-sm leading-relaxed">
              I am your Clinical Intelligence Agent. Run deep SQL analytics, monitor patient health trends, or analyze medical logistics with precision.
            </p>
            <div className="flex gap-2 flex-wrap justify-center pt-4">
              {['Inventory status', 'Patient demographics', 'Lab results'].map(chip => (
                <button key={chip} className="px-4 py-2 bg-white/5 border border-white/10 rounded-md text-[11px] font-semibold text-gray-400 hover:bg-white/10 hover:text-white transition-all">
                  {chip}
                </button>
              ))}
            </div>
          </div>
        )}

      {messages.map((msg, idx) => (
        <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[85%] space-y-4 ${msg.role === 'ai' ? 'animate-fade-in-up' : ''}`}>
              {msg.content && (
                <div className={
                  msg.role === 'user' 
                    ? 'chat-bubble-user' 
                    : msg.isError 
                      ? 'py-3.5 px-4 rounded-md border border-red-500/40 flex gap-4 items-start bg-red-500/[0.02]'
                      : 'py-2'
                }>
                  {msg.isError && <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={28} strokeWidth={2} />}
                  <div className="max-w-none">
                    {msg.role === 'ai' ? (
                      <div className="max-w-none">
                        {renderMarkdown(msg.content, msg.isError)}
                      </div>
                    ) : (
                      <p className="text-[13px] leading-relaxed whitespace-pre-wrap font-medium">
                        {msg.content}
                      </p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Dynamic Data Table */}
              <div className="w-full">
                {msg.data && <DataTable data={msg.data} />}
              </div>
              
              {/* Tool Metadata */}
              {msg.nextStep && (
                <div className="flex items-center flex-wrap gap-4 mt-3">
                  <div className="flex items-center gap-2 bg-white/[0.03] px-3 py-1 rounded-md border border-white/5">
                    {msg.nextStep === 'SQL' ? <Database size={12} className="text-gray-500" /> : <Search size={12} className="text-gray-500" />}
                    <span className="text-[9px] font-bold tracking-wider uppercase text-gray-500">{msg.nextStep} Output</span>
                  </div>
                  
                  {msg.logs && (
                    <button 
                      onClick={() => {
                        if (isTraceOpen && traceLogs === msg.logs) {
                          setIsTraceOpen(false);
                        } else {
                          setTraceLogs(msg.logs);
                          setIsTraceOpen(true);
                        }
                      }}
                      className={`flex items-center gap-2 border px-3 py-1 rounded-md transition-all cursor-pointer shadow-sm ${
                        isTraceOpen && traceLogs === msg.logs
                        ? 'bg-clinical-blue/20 border-clinical-blue text-clinical-blue'
                        : 'bg-white/[0.05] border-white/10 hover:bg-white/[0.08] text-gray-300'
                      }`}
                    >
                      <Brain size={12} className={isTraceOpen && traceLogs === msg.logs ? 'text-clinical-blue' : 'text-gray-400'} />
                      <span className="text-[9px] font-bold uppercase tracking-wider">
                        Reasoning Trace
                      </span>
                    </button>
                  )}

                  {msg.tool_query && msg.tool_query.toUpperCase().includes("SELECT") && (
                    <button 
                      onClick={() => onExport(msg.tool_query)}
                      className="flex items-center gap-2 border px-3 py-1 rounded-md transition-all cursor-pointer shadow-sm bg-white/[0.05] border-white/10 hover:bg-white/[0.08] text-gray-300"
                    >
                      <Download size={12} className="text-gray-400" />
                      <span className="text-[9px] font-bold uppercase tracking-wider">
                        Export Full CSV
                      </span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
      ))}


      {isLoading && (
        <div className="flex justify-start animate-fade-in pl-2">
          <div className="flex gap-4 items-center text-clinical-blue/60 italic text-[13px] font-medium">
            <div className="flex gap-1.5">
              <span className="w-1.5 h-1.5 bg-clinical-blue rounded-full animate-bounce [animation-duration:1s]"></span>
              <span className="w-1.5 h-1.5 bg-clinical-blue rounded-full animate-bounce [animation-duration:1s] [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 bg-clinical-blue rounded-full animate-bounce [animation-duration:1s] [animation-delay:0.4s]"></span>
            </div>
            Clinical Engine analyzing medical database...
          </div>
        </div>
      )}

      </div>
    </div>
  );
};

export default MessageList;
