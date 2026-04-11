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

const renderMarkdown = (text) => {
  if (!text) return null;
  
  // Split by lines to handle headers
  const lines = text.split('\n');
  
  return lines.map((line, i) => {
    // Headers: ### 
    if (line.startsWith('###')) {
      return <h3 key={i} className="text-clinical-blue font-bold text-lg mt-6 mb-2">{line.replace('###', '').trim()}</h3>;
    }
    if (line.startsWith('##')) {
      return <h2 key={i} className="text-clinical-blue font-bold text-xl mt-8 mb-3">{line.replace('##', '').trim()}</h2>;
    }
    
    // Bold: **text**
    const parts = line.split(/(\*\*.*?\*\*)/g);
    const renderedLine = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j} className="font-bold text-dark-grey">{part.slice(2, -2)}</strong>;
      }
      return part;
    });

    return <p key={i} className="mb-3">{renderedLine}</p>;
  });
};

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [modelName, setModelName] = useState("Loading...");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [availableModels, setAvailableModels] = useState([]);
  const scrollRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const [configRes, modelsRes] = await Promise.all([
          axios.get(`${API_BASE}/config`),
          axios.get(`${API_BASE}/models`)
        ]);
        
        setAvailableModels(modelsRes.data);
        setModelName(configRes.data.model_name);
        setSelectedModel(configRes.data.model_name);
        setSelectedProvider(configRes.data.provider);
      } catch (error) {
        console.error("Fetch error:", error);
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
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/query`, { 
        query: input,
        model: selectedModel,
        provider: selectedProvider
      });
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

          <div className="p-4 border-t border-gray-50 flex flex-col gap-2 bg-gray-50/30">
            <div className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-1">Inference Engine</div>
            <select 
              value={`${selectedProvider}:${selectedModel}`}
              onChange={(e) => {
                const [provider, modelId] = e.target.value.split(':');
                setSelectedProvider(provider);
                setSelectedModel(modelId);
                setModelName(availableModels.find(m => m.id === modelId)?.name || modelId);
              }}
              className="w-full bg-transparent border border-gray-100 rounded-md py-1 px-1.5 text-[12px] text-clinical-blue font-medium focus:outline-none cursor-pointer transition-all"
            >
              {availableModels.map((m, idx) => (
                <option key={idx} value={`${m.provider}:${m.id}`}>
                  {m.name}
                </option>
              ))}
            </select>
            <div className="text-[9px] text-gray-400 mt-2 border-t border-gray-100 pt-1 flex justify-between items-center">
              <span>Build v1.2.5 • Stable</span>
              <Activity size={10} className="text-green-500" />
            </div>
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
                    {msg.data && Array.isArray(msg.data) && msg.data.length > 0 && (
                      <div className="overflow-x-auto w-full border border-gray-100 rounded-lg bg-white custom-scrollbar">
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
          <div className="w-full pt-6 pb-10 px-6 flex flex-col items-center border-t border-gray-100 bg-off-white/80 backdrop-blur-sm self-end">
            <div className="w-full max-w-3xl relative">
              <form onSubmit={handleSend} className="relative group">
                <textarea 
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    e.target.style.height = 'auto';
                    e.target.style.height = `${e.target.scrollHeight}px`;
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend(e);
                    }
                  }}
                  placeholder="Query clinical data..." 
                  rows={1}
                  className="w-full pl-6 pr-16 pt-4 pb-14 bg-white border border-gray-100 rounded-2xl focus:outline-none focus:border-clinical-blue/30 transition-all duration-300 placeholder:text-gray-300 resize-none max-h-64 overflow-y-hidden"
                />

                <button 
                  type="submit"
                  className="absolute right-3 bottom-5 p-2 bg-clinical-blue text-white rounded-md hover:brightness-90 transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-40 flex items-center justify-center shadow-sm" 
                  disabled={isLoading || !input.trim()}
                >
                  <Send size={18} fill="white" />
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

