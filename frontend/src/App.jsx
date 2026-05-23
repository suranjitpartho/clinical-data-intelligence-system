import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// Components
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MessageList from './components/Chat/MessageList';
import ChatInput from './components/Chat/ChatInput';
import TraceSidebar from './components/TraceSidebar';
import AnalyticsView from './components/Analytics';


const API_BASE = window.location.port === "5173" ? "http://localhost:8000" : "";

function App() {
  const [currentView, setCurrentView] = useState('chat'); // 'chat' or 'analytics'
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [threadId, setThreadId] = useState(() => `session_${Math.random().toString(36).slice(2, 11)}`);
  const [threads, setThreads] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [modelName, setModelName] = useState("Loading...");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [availableModels, setAvailableModels] = useState([]);
  const [isTraceOpen, setIsTraceOpen] = useState(false);
  const [traceLogs, setTraceLogs] = useState("");
  const [analyticsData, setAnalyticsData] = useState(null);
  const [operationalData, setOperationalData] = useState(null);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(false);
  const [analyticsSubView, setAnalyticsSubView] = useState('traces'); // 'traces' or 'operational'
  const [analyticsRange, setAnalyticsRange] = useState(7);      // days: 7, 15, 30
  const [analyticsPage, setAnalyticsPage] = useState(1);
  const [analyticsPageSize] = useState(10);

  const [streamingContent, setStreamingContent] = useState("");
  const [currentNode, setCurrentNode] = useState("");
  const [threadsHasMore, setThreadsHasMore] = useState(false);
  const streamingRef = useRef("");
  const threadsPageRef = useRef(1);

  const scrollRef = useRef(null);

  const fetchThreads = async (page = 1) => {
    try {
      const res = await axios.get(`${API_BASE}/threads`, {
        params: { page, page_size: 25 }
      });
      const data = res.data || {};
      if (page === 1) {
        setThreads(data.threads || []);
      } else {
        setThreads(prev => [...prev, ...(data.threads || [])]);
      }
      setThreadsHasMore(data.has_more || false);
      threadsPageRef.current = page;
    } catch (error) {
      console.error("Failed to fetch threads:", error);
    }
  };

  const loadMoreThreads = () => {
    fetchThreads(threadsPageRef.current + 1);
  };

  const selectThread = async (tid) => {
    setThreadId(tid);
    setCurrentView('chat');
    setIsTraceOpen(false);
    try {
      const res = await axios.get(`${API_BASE}/threads/${tid}`);
      const msgs = (res.data.messages || []).map(m => ({
        role: m.role,
        content: m.content,
        data: m.data_results || null,
        tool_query: m.tool_query || null,
        nextStep: m.next_step || null,
      }));
      setMessages(msgs);
      setHistory(res.data.messages || []);
    } catch (error) {
      console.error("Failed to load thread:", error);
    }
  };

  const createNewChat = () => {
    setMessages([]);
    setHistory([]);
    setIsTraceOpen(false);
    setCurrentView('chat');
    setThreadId(`session_${Math.random().toString(36).slice(2, 11)}`);
  };

  const [isSyncing, setIsSyncing] = useState(false);

  const fetchAnalytics = async (days = analyticsRange, page = analyticsPage, pageSize = analyticsPageSize) => {
    setIsAnalyticsLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/analytics`, {
        params: { days, page, page_size: pageSize }
      });
      if (res.data && !res.data.error) {
        setAnalyticsData(prev => {
          const isPaginating = page > 1;
          return {
            ...res.data,
            summary: (isPaginating && prev?.summary) ? prev.summary : res.data.summary
          };
        });
      }
    } catch (error) {
      console.error("Analytics fetch error:", error);
    } finally {
      setIsAnalyticsLoading(false);
    }
  };

  const fetchOperationalAnalytics = async (days = analyticsRange) => {
    setIsAnalyticsLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/analytics/operational`, {
        params: { days }
      });
      if (res.data) {
        setOperationalData(res.data);
      }
    } catch (error) {
      console.error("Operational analytics fetch error:", error);
      setOperationalData({ error: error.message });
    } finally {
      setIsAnalyticsLoading(false);
    }
  };

  const handleSyncAnalytics = async () => {
    setIsSyncing(true);
    try {
      await axios.post(`${API_BASE}/analytics/sync`, null, {
        params: { days: analyticsRange }
      });
      // After sync, immediately refresh local views from DB
      await Promise.all([
        fetchAnalytics(analyticsRange, 1, analyticsPageSize),
        fetchOperationalAnalytics(analyticsRange)
      ]);
    } catch (error) {
      console.error("Sync error:", error);
      alert("Intelligence sync failed. Verify Langfuse connectivity.");
    } finally {
      setIsSyncing(false);
    }
  };

  // Refetch when range or page changes
  useEffect(() => {
    if (currentView === 'analytics') {
      if (analyticsSubView === 'traces') {
        fetchAnalytics(analyticsRange, analyticsPage, analyticsPageSize);
      } else {
        fetchOperationalAnalytics(analyticsRange);
      }
    }
  }, [currentView, analyticsRange, analyticsPage, analyticsSubView]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading, streamingContent]);

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
    fetchThreads();
  }, []);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);

    const originalInput = input;
    setInput("");
    setIsLoading(true);
    streamingRef.current = "";
    setStreamingContent("");
    setCurrentNode("");

    try {
      const response = await fetch(`${API_BASE}/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: originalInput,
          model: selectedModel,
          provider: selectedProvider,
          thread_id: threadId,
          history: history
        })
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.trim()) continue;

          const lines = part.split("\n");
          let event = "";
          let dataRaw = "";

          for (const line of lines) {
            if (line.startsWith("event: ")) event = line.slice(7).trim();
            else if (line.startsWith("data: ")) dataRaw = line.slice(6);
          }

          if (!dataRaw) continue;
          const data = JSON.parse(dataRaw);

          if (event === "node_start") {
            setCurrentNode(data.node);
          } else if (event === "token") {
            streamingRef.current += data.content;
            setStreamingContent(streamingRef.current);
          } else if (event === "done") {
            const aiResponse = {
              role: "ai",
              content: streamingRef.current,
              data: data.data_results,
              nextStep: data.next_step,
              tool_query: data.tool_query,
              logs: data.logs,
              isError: false
            };
            setMessages(prev => [...prev, aiResponse]);
            if (data.history) setHistory(data.history);
            streamingRef.current = "";
            setStreamingContent("");
            setCurrentNode("");
            fetchThreads();
          } else if (event === "error") {
            setMessages(prev => [...prev, {
              role: "ai",
              content: data.message || "An error occurred.",
              isError: true
            }]);
            streamingRef.current = "";
            setStreamingContent("");
            setCurrentNode("");
          }
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
      setMessages(prev => [...prev, {
        role: "ai",
        content: "Error: Could not connect to the Clinical Intelligence backend.",
        isError: true
      }]);
    } finally {
      setIsLoading(false);
      setCurrentNode("");
    }
  };

  const handleExport = async (sql) => {
    if (!sql) return;
    try {
      const response = await axios.post(`${API_BASE}/export-csv`, { sql }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `clinical_export_${new Date().getTime()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Failed to export CSV. Please try again.");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-dark-bg font-sans text-gray-100 overflow-hidden relative">
      <Header />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Ambient background glows for depth */}
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-clinical-blue/10 rounded-full blur-[140px] pointer-events-none animate-glow-pulse"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-clinical-blue/5 rounded-full blur-[120px] pointer-events-none"></div>

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
          onNewChat={createNewChat}
          threads={threads}
          hasMore={threadsHasMore}
          onLoadMore={loadMoreThreads}
          activeThreadId={threadId}
          onSelectThread={selectThread}
        />

        <main className="flex-1 flex flex-col overflow-hidden relative bg-black/10">
          {currentView === 'chat' ? (


            <>
              <MessageList
                messages={messages}
                isLoading={isLoading}
                streamingContent={streamingContent}
                currentNode={currentNode}
                scrollRef={scrollRef}
                isTraceOpen={isTraceOpen}
                setIsTraceOpen={setIsTraceOpen}
                traceLogs={traceLogs}
                setTraceLogs={setTraceLogs}
                onExport={handleExport}
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
              operationalData={operationalData}
              subView={analyticsSubView}
              setSubView={setAnalyticsSubView}
              isLoading={isAnalyticsLoading}
              isSyncing={isSyncing}
              onSync={handleSyncAnalytics}
              onBack={() => setCurrentView('chat')}
              range={analyticsRange}
              onRangeChange={(days) => { setAnalyticsRange(days); setAnalyticsPage(1); }}
              currentPage={analyticsPage}
              onPageChange={setAnalyticsPage}
              pageSize={analyticsPageSize}
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
