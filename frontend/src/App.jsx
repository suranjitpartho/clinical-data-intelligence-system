import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Send, 
  Bot, 
  User, 
  Database, 
  Search, 
  Stethoscope, 
  PlusCircle,
  MessageSquare,
  Activity
} from 'lucide-react';

const API_BASE = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [modelName, setModelName] = useState("Loading...");
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await axios.get(`${API_BASE}/config`);
        setModelName(response.data.model_name);
      } catch (error) {
        setModelName("Unknown Model");
      }
    };
    fetchConfig();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/query`, { query: input });
      const aiResponse = { 
        role: 'ai', 
        content: response.data.final_answer,
        data: response.data.data_results,
        nextStep: response.data.next_step
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: "Error: Could not connect to the Clinical Intelligence backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-off-white font-sans text-dark-grey">
      {/* Top Menu Bar */}
      <header className="w-full border-b border-gray-100 bg-white/80 backdrop-blur-sm z-20 p-4 px-8 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 pr-6 border-r border-gray-100">
            <Bot className="text-clinical-blue animate-beep" size={24} />
            <h1 className="font-display font-medium tracking-tight text-lg">Clinical Data Intelligence System</h1>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-xs text-right">
            <div className="font-bold">Suranjit Das</div>
            <div className="text-gray-400">AI Engineer</div>
          </div>
          <div className="w-8 h-8 rounded-full bg-dark-grey flex items-center justify-center text-white text-xs">SD</div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-100 flex flex-col hidden md:flex">
          <div className="p-4 flex-1">
            <button className="w-full flex items-center justify-center gap-2 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-100 rounded-lg text-sm font-medium transition-all mb-6">
              <PlusCircle size={16} /> New Consultation
            </button>
            
            <nav className="space-y-1">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-3 mb-2">Recent</div>
              <div className="px-3 py-2 bg-blue-50/50 text-clinical-blue rounded-md flex items-center gap-3 text-sm font-medium cursor-pointer">
                <MessageSquare size={16} />
                <span className="truncate">Department Statistics</span>
              </div>
              <div className="px-3 py-2 hover:bg-gray-50 rounded-md flex items-center gap-3 text-sm text-gray-600 cursor-pointer">
                <MessageSquare size={16} />
                <span className="truncate">Blood Test Analysis</span>
              </div>
            </nav>
          </div>

          <div className="p-4 border-t border-gray-50 flex flex-col gap-1 bg-gray-50/30">
            <div className="text-[10px] text-gray-400 font-normal uppercase tracking-widest mb-1">Model</div>
            <div className="text-[12px] text-clinical-blue font-medium tracking-tight">
              {modelName}
            </div>
            <div className="text-[9px] text-gray-400 mt-2 border-t border-gray-100 pt-1">Build v1.2.4 • Stable</div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col bg-off-white overflow-hidden">
          {/* Full-width scroll container */}
          <div className="flex-1 w-full overflow-y-auto" ref={scrollRef}>
            <div className="max-w-3xl mx-auto w-full p-4 space-y-6 pb-8">
              
              {/* Empty State Welcome Screen */}
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
                <div className="max-w-[85%] space-y-2">
                    {msg.content && (
                      <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    )}
                    
                    {/* Dynamic Data Table */}
                    {msg.data && Array.isArray(msg.data) && msg.data.length > 0 && (
                      <div className="overflow-hidden border border-gray-100 rounded-lg bg-white min-w-[300px]">
                        <table className="min-w-full divide-y divide-gray-100 text-[11px]">
                          <thead className="bg-gray-50">
                            <tr>
                              {Object.keys(msg.data[0]).map((key) => (
                                <th key={key} className="px-3 py-2 text-left font-bold text-gray-400 uppercase tracking-wider">
                                  {key.replace('_', ' ')}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {msg.data.slice(0, 10).map((row, rIdx) => (
                              <tr key={rIdx} className="hover:bg-gray-50/50 transition-colors">
                                {Object.values(row).map((val, cIdx) => (
                                  <td key={cIdx} className="px-3 py-2 text-gray-600 font-medium whitespace-nowrap">
                                    {typeof val === 'number' && !Number.isInteger(val) ? val.toFixed(2) : val?.toString() || '-'}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                    
                    {/* Tool Metadata */}
                    {msg.nextStep && (
                      <div className="flex items-center gap-2 px-1">
                        {msg.nextStep === 'SQL' ? <Database size={12} className="text-blue-500" /> : <Search size={12} className="text-orange-500" />}
                        <span className="text-[10px] font-bold text-gray-400">Tool: {msg.nextStep} engine</span>
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
          {/* Input Bar */}
          <div className="w-full p-6 flex flex-col items-center border-t border-gray-100 bg-off-white/80 backdrop-blur-sm self-end">
            <div className="w-full max-w-3xl relative">
              <form onSubmit={handleSend} className="relative group">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Query clinical data..." 
                  className="w-full pl-6 pr-14 py-4 bg-white border border-gray-200 rounded-2xl focus:outline-none focus:border-gray-300 focus:shadow-centered transition-all duration-300 placeholder:text-gray-300"
                />

              <button className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-clinical-blue text-white rounded-xl hover:opacity-90 transition-all disabled:opacity-50 shadow-sm flex items-center justify-center" disabled={isLoading}>
                <Send size={18} fill="currentColor" strokeWidth={2.5} />
              </button>
            </form>
            <p className="text-center text-[10px] text-gray-400 mt-4">
              CONFIDENTIAL: For authorized clinical personnel use only.
            </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;

