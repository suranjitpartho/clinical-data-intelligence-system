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
  const [messages, setMessages] = useState([
    { role: 'ai', content: "Hello Dr. Dashboard. I am CLARA, your Clinical Assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

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
    <div className="flex h-screen bg-off-white font-sans text-dark-grey">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col hidden md:flex">
        <div className="p-6 flex items-center gap-2 border-b border-gray-100">
          <Stethoscope className="text-clinical-blue" size={24} />
          <h1 className="font-bold tracking-tight text-lg">CDIS <span className="text-gray-400 font-normal">v1.2</span></h1>
        </div>
        
        <div className="p-4 flex-1">
          <button className="w-full flex items-center justify-center gap-2 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg text-sm font-medium transition-all mb-6">
            <PlusCircle size={16} /> New Consultation
          </button>
          
          <nav className="space-y-1">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-3 mb-2">Recent</div>
            <div className="px-3 py-2 bg-blue-50 text-clinical-blue rounded-md flex items-center gap-3 text-sm font-medium cursor-pointer">
              <MessageSquare size={16} />
              <span className="truncate">Department Statistics</span>
            </div>
            <div className="px-3 py-2 hover:bg-gray-50 rounded-md flex items-center gap-3 text-sm text-gray-600 cursor-pointer">
              <MessageSquare size={16} />
              <span className="truncate">Blood Test Analysis</span>
            </div>
          </nav>
        </div>

        <div className="p-4 border-t border-gray-100 italic text-[10px] text-gray-400">
          Powered by Native M5 MLX & Llama-3
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col items-center">
        <header className="w-full border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10 p-4 px-8 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Activity className="text-green-500 animate-pulse" size={18} />
            <span className="text-sm font-bold">System Online</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-xs text-right">
              <div className="font-bold">Dr. Parth Das</div>
              <div className="text-gray-400">Lead Clinician</div>
            </div>
            <div className="w-8 h-8 rounded-full bg-dark-grey flex items-center justify-center text-white text-xs">PD</div>
          </div>
        </header>

        <div className="flex-1 w-full max-w-3xl overflow-y-auto p-4 space-y-6" ref={scrollRef}>
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'user' ? 'bg-clinical-blue text-white' : 'bg-white border border-gray-100 shadow-sm text-dark-grey'}`}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className="space-y-2">
                  <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  
                  {/* Tool Metadata */}
                  {msg.nextStep && (
                    <div className="flex items-center gap-2 px-1">
                      {msg.nextStep === 'SQL' ? <Database size={12} className="text-blue-500" /> : <Search size={12} className="text-orange-500" />}
                      <span className="text-[10px] font-bold text-gray-400">Source: {msg.nextStep} engine</span>
                    </div>
                  )}
                </div>
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
                CLARA is analyzing medical database...
              </div>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="w-full max-w-3xl p-6 relative">
          <form onSubmit={handleSend} className="relative group">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Query clinical data (e.g., 'How many patients are scheduled today?')" 
              className="w-full pl-6 pr-14 py-4 bg-white border border-gray-200 rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-clinical-blue/20 focus:border-clinical-blue transition-all"
            />
            <button className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-dark-grey text-white rounded-xl hover:bg-gray-700 transition-colors disabled:opacity-50" disabled={isLoading}>
              <Send size={18} />
            </button>
          </form>
          <p className="text-center text-[10px] text-gray-400 mt-4">
            CONFIDENTIAL: For authorized clinical personnel use only. System logs all interactions.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
