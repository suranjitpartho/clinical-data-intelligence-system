import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { useConfig } from './hooks/useConfig';
import { useThreads } from './hooks/useThreads';
import { useChat } from './hooks/useChat';
import { useAnalytics } from './hooks/useAnalytics';
import LoginPage from './components/Auth/LoginPage';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MessageList from './components/Chat/MessageList';
import ChatInput from './components/Chat/ChatInput';
import TraceSidebar from './components/TraceSidebar';
import AnalyticsView from './components/Analytics';
import ClarifyCard from './components/Chat/ClarifyCard';

function App() {
  const { user, isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();

  // UI state
  const [currentView, setCurrentView] = useState('chat');
  const [input, setInput] = useState('');
  const [isTraceOpen, setIsTraceOpen] = useState(false);
  const [traceLogs, setTraceLogs] = useState('');
  const [analyticsSubView, setAnalyticsSubView] = useState('traces');

  const scrollRef = useRef(null);

  // Feature hooks
  const config = useConfig();
  const threads = useThreads(isAuthenticated);
  const chat = useChat(config.selectedModel, config.selectedProvider);
  const analytics = useAnalytics(currentView, analyticsSubView);

  // Coordination between hooks
  const handleSend = (e) => {
    e?.preventDefault();
    chat.handleSend(input);
    setInput('');
  };

  const selectThread = async (tid) => {
    setCurrentView('chat');
    setIsTraceOpen(false);
    await chat.loadThread(tid);
  };

  const createNewChat = () => {
    chat.resetChat();
    setIsTraceOpen(false);
    setCurrentView('chat');
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chat.messages, chat.isLoading, chat.streamingContent]);

  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-bg text-gray-500 text-sm">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border border-clinical-blue border-t-transparent rounded-full animate-spin"></div>
          Signing in...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="flex flex-col h-screen bg-dark-bg font-sans text-gray-100 overflow-hidden relative">
      <Header user={user} onLogout={logout} />

      <div className="flex flex-1 overflow-hidden relative">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-clinical-blue/10 rounded-full blur-[140px] pointer-events-none animate-glow-pulse"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-clinical-blue/5 rounded-full blur-[120px] pointer-events-none"></div>

        <Sidebar
          availableModels={config.availableModels}
          selectedModel={config.selectedModel}
          selectedProvider={config.selectedProvider}
          setSelectedModel={config.setSelectedModel}
          setSelectedProvider={config.setSelectedProvider}
          modelName={config.modelName}
          setModelName={config.setModelName}
          currentView={currentView}
          setCurrentView={setCurrentView}
          onNewChat={createNewChat}
          threads={threads.threads}
          hasMore={threads.threadsHasMore}
          currentPage={threads.currentPage}
          onPageChange={threads.goToPage}
          activeThreadId={chat.threadId}
          onSelectThread={selectThread}
        />

        <main className="flex-1 flex flex-col overflow-hidden relative bg-black/10">
          {currentView === 'chat' ? (
            <>
              <MessageList
                messages={chat.messages}
                isLoading={chat.isLoading}
                streamingContent={chat.streamingContent}
                currentNode={chat.currentNode}
                scrollRef={scrollRef}
                isTraceOpen={isTraceOpen}
                setIsTraceOpen={setIsTraceOpen}
                traceLogs={traceLogs}
                setTraceLogs={setTraceLogs}
                onExport={chat.handleExport}
                pendingQuestions={chat.pendingQuestions}
              />

              {chat.isClarifying && chat.pendingQuestions ? (
                <div className="w-full pt-2.5 pb-2 px-6 flex flex-col items-center bg-[#080C14]/90 backdrop-blur-2xl self-end z-20">
                  <div className="w-full max-w-3xl">
                    <ClarifyCard
                      questions={chat.pendingQuestions}
                      onSubmit={chat.handleClarifySubmit}
                    />
                  </div>
                </div>
              ) : (
                <ChatInput
                  input={input}
                  setInput={setInput}
                  handleSend={handleSend}
                  isLoading={chat.isLoading}
                />
              )}
            </>
          ) : (
            <AnalyticsView
              metrics={analytics.analyticsData}
              operationalData={analytics.operationalData}
              subView={analyticsSubView}
              setSubView={setAnalyticsSubView}
              isLoading={analytics.isAnalyticsLoading}
              isSyncing={analytics.isSyncing}
              syncStatus={analytics.syncStatus}
              onSync={analytics.handleSyncAnalytics}
              onBack={() => setCurrentView('chat')}
              range={analytics.analyticsRange}
              onRangeChange={analytics.handleRangeChange}
              currentPage={analytics.analyticsPage}
              onPageChange={analytics.setAnalyticsPage}
              pageSize={analytics.analyticsPageSize}
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
