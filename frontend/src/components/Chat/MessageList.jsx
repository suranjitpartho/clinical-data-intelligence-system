import React from 'react';
import { Database, Search, Brain } from 'lucide-react';
import { renderMarkdown } from '../../utils/markdown-renderer';
import DataTable from './DataTable';

const MessageList = ({ messages, isLoading, scrollRef, setIsTraceOpen, setTraceLogs }) => {
  return (
    <div className="flex-1 w-full overflow-y-auto" ref={scrollRef}>
      <div className="max-w-3xl mx-auto w-full p-4 space-y-6 pb-8">
        
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center pt-32 pb-16 space-y-4 animate-fade-in">
            <h2 className="text-3xl font-display font-normal text-dark-grey tracking-tight">How can I help you today?</h2>
            <p className="text-gray-400 text-center max-w-md">
              I am your Clinical AI Agent. Run deep SQL analytics on patients, inventory, or financial data.
            </p>
          </div>
        )}

      {messages.map((msg, idx) => (
        <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[85%] space-y-2 ${msg.role === 'ai' ? 'animate-fade-in-up' : ''}`}>
              {msg.content && (
                <div className={msg.role === 'user' ? 'chat-bubble-user' : 'py-2 px-1'}>
                  <div className={`prose-container max-w-none ${msg.role === 'ai' ? 'text-dark-grey' : 'text-white'}`}>
                    {msg.role === 'ai' ? (
                      renderMarkdown(msg.content)
                    ) : (
                      <p className="text-[14px] leading-[1.6] whitespace-pre-wrap font-normal">
                        {msg.content}
                      </p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Dynamic Data Table */}
              {msg.data && <DataTable data={msg.data} />}
              
              {/* Tool Metadata */}
              {msg.nextStep && (
                <div className="flex items-center flex-wrap gap-2 px-1">
                  <div className="flex items-center gap-1.5 text-gray-400">
                    {msg.nextStep === 'SQL' ? <Database size={12} className="text-blue-500" /> : <Search size={12} className="text-orange-500" />}
                    <span className="text-[10px] font-bold tracking-tight uppercase">Decision: {msg.nextStep} engine</span>
                  </div>
                  
                  {msg.logs && (
                    <button 
                      onClick={() => {
                        setTraceLogs(msg.logs);
                        setIsTraceOpen(true);
                      }}
                      className="flex items-center gap-1.5 bg-gray-50 border border-gray-100 px-2 py-0.5 rounded-full hover:bg-gray-100/70 transition-colors cursor-pointer group"
                    >
                      <Brain size={10} className="text-gray-400 group-hover:text-dark-grey" />
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter group-hover:text-dark-grey">
                        Reasoning Trace
                      </span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
      ))}

      {isLoading && (
        <div className="flex justify-start animate-fade-in">
          <div className="flex gap-3 items-center text-gray-400 italic text-sm">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
            Clinical AI Agent is analyzing medical database...
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default MessageList;
