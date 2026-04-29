import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// Components
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MessageList from './components/Chat/MessageList';
import ChatInput from './components/Chat/ChatInput';
import TraceSidebar from './components/TraceSidebar';
import AnalyticsView from './components/AnalyticsView';

const API_BASE = window.location.port === "5173" ? "http://localhost:8000" : "";

function App() {
  const [currentView, setCurrentView] = useState('chat'); // 'chat' or 'analytics'
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]); 
  const [threadId] = useState(() => `session_${Math.random().toString(36).slice(2, 11)}`);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [modelName, setModelName] = useState("Loading...");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [availableModels, setAvailableModels] = useState([]);
  const [isTraceOpen, setIsTraceOpen] = useState(false);
  const [traceLogs, setTraceLogs] = useState("");
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(false);
  
  const scrollRef = useRef(null);

  const fetchAnalytics = async () => {
    setIsAnalyticsLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/analytics`);
      setAnalyticsData(res.data);
    } catch (error) {
      console.error("Analytics fetch error:", error);
    } finally {
      setIsAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    if (currentView === 'analytics') {
      fetchAnalytics();
    }
  }, [currentView]); // Only fetch when switching to analytics view

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const [configRes, modelsRes] = await Promise.all([
          axios.get(`${API_BASE}/config`),
          axios.get(`${API_BASE}/models`)
        ]);
        
        setAvailableModels(modelsRes.data);
        const currentModel = modelsRes.data.find(m => m.id === configRes.data.model_name);
        setModelName(currentModel ? currentModel.name : configRes.data.model_name);
        setSelectedModel(configRes.data.model_name);
        setSelectedProvider(configRes.data.provider);
      } catch (error) {
        console.error("Fetch error:", error);
      }
    };
    fetchConfig();
  }, []);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    
    const originalInput = input;
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/query`, { 
        query: originalInput,
        model: selectedModel,
        provider: selectedProvider,
        thread_id: threadId,
        history: history
      });
      
      const aiResponse = { 
        role: 'ai', 
        content: response.data.final_answer,
        data: response.data.data_results,
        nextStep: response.data.next_step,
        logs: response.data.logs
      };
      
      setMessages(prev => [...prev, aiResponse]);
      if (response.data.history) {
        setHistory(response.data.history);
      }
      await fetchAnalytics();
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: "Error: Could not connect to the Clinical Intelligence backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-off-white font-sans text-dark-grey">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          availableModels={availableModels}
          selectedModel={selectedModel}
          selectedProvider={selectedProvider}
          setSelectedModel={setSelectedModel}
          setSelectedProvider={setSelectedProvider}
          modelName={modelName}
          setModelName={setModelName}
          currentView={currentView}
          setCurrentView={setCurrentView}
        />

        <main className="flex-1 flex flex-col bg-off-white overflow-hidden relative">
          {currentView === 'chat' ? (
            <>
              <MessageList 
                messages={messages} 
                isLoading={isLoading} 
                scrollRef={scrollRef} 
                setIsTraceOpen={setIsTraceOpen}
                setTraceLogs={setTraceLogs}
              />
              
              <ChatInput 
                input={input}
                setInput={setInput}
                handleSend={handleSend}
                isLoading={isLoading}
              />
            </>
          ) : (
            <AnalyticsView 
              metrics={analyticsData} 
              isLoading={isAnalyticsLoading}
              onBack={() => setCurrentView('chat')} 
            />
          )}
        </main>

        <TraceSidebar 
          isOpen={isTraceOpen} 
          setIsOpen={setIsTraceOpen} 
          logs={traceLogs} 
        />
      </div>
    </div>
  );
}

export default App;
