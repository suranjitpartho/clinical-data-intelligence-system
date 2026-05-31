import { useState, useRef, useCallback } from 'react';
import { parseSSEStream } from '../utils/sse-parser';
import api from '../utils/api';

export function useChat(selectedModel, selectedProvider) {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [threadId, setThreadId] = useState(() => `session_${Math.random().toString(36).slice(2, 11)}`);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [currentNode, setCurrentNode] = useState("");
  const [pendingQuestions, setPendingQuestions] = useState(null);
  const [isClarifying, setIsClarifying] = useState(false);
  const [requestId, setRequestId] = useState(null);

  const streamingRef = useRef("");

  const resetStreaming = () => {
    streamingRef.current = "";
    setStreamingContent("");
    setCurrentNode("");
  };

  const handleSend = useCallback(async (inputText) => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = { role: 'user', content: inputText };
    setMessages(prev => [...prev, userMessage]);

    setIsLoading(true);
    resetStreaming();

    try {
      const result = await parseSSEStream('/query/stream', {
        query: inputText,
        model: selectedModel,
        provider: selectedProvider,
        thread_id: threadId,
        history: history,
      }, {
        onNodeStart: (node) => {
          setCurrentNode(node);
        },
        onToken: (content) => {
          streamingRef.current += content;
          setStreamingContent(streamingRef.current);
        },
        onDone: (data) => {
          const content = streamingRef.current;
          const aiResponse = {
            role: "ai",
            content: content,
            data: data.data_results,
            nextStep: data.next_step,
            tool_query: data.tool_query,
            logs: data.logs,
            isError: data.is_error || false,
            error_code: data.error_code || null,
          };
          setMessages(prev => [...prev, aiResponse]);
          if (data.history) setHistory(data.history);
          resetStreaming();
        },
        onClarify: (data) => {
          setPendingQuestions(data.questions);
          setIsClarifying(true);
          setRequestId(data.request_id || null);
          resetStreaming();
          setIsLoading(false);
        },
        onError: (data) => {
          setMessages(prev => [...prev, {
            role: "ai",
            content: data.message || "An error occurred.",
            isError: true,
            error_code: data.code || "UNKNOWN_ERROR",
            logs: data.logs || "",
          }]);
          resetStreaming();
        },
      });
    } catch (error) {
      console.error("Stream error:", error);
      setMessages(prev => [...prev, {
        role: "ai",
        content: "Error: Could not connect to the Clinical Intelligence backend.",
        isError: true,
        error_code: "NETWORK_ERROR",
      }]);
    } finally {
      setIsLoading(false);
      setCurrentNode("");
    }
  }, [selectedModel, selectedProvider, threadId, history, isLoading]);

  const handleClarifySubmit = useCallback(async (answers) => {
    setIsLoading(true);
    try {
      const body = {
        thread_id: threadId,
        answers: answers,
        model: selectedModel,
        provider: selectedProvider,
      };
      if (requestId) body.request_id = requestId;

      await parseSSEStream(`/threads/${threadId}/resume`, body, {
        onNodeStart: (node) => {
          setCurrentNode(node);
        },
        onToken: (content) => {
          streamingRef.current += content;
          setStreamingContent(streamingRef.current);
        },
        onDone: (data) => {
          const content = streamingRef.current;
          const aiResponse = {
            role: "ai",
            content: content,
            data: data.data_results,
            nextStep: data.next_step,
            tool_query: data.tool_query,
            logs: data.logs,
            isError: data.is_error || false,
            error_code: data.error_code || null,
          };
          setMessages(prev => [...prev, aiResponse]);
          if (data.history) setHistory(data.history);
          resetStreaming();
          setPendingQuestions(null);
          setIsClarifying(false);
          setRequestId(null);
        },
        onError: (data) => {
          setMessages(prev => [...prev, {
            role: "ai",
            content: data.message || "An error occurred.",
            isError: true,
            error_code: data.code || "UNKNOWN_ERROR",
            logs: data.logs || "",
          }]);
          resetStreaming();
          setPendingQuestions(null);
          setIsClarifying(false);
          setRequestId(null);
        },
      });
    } catch (error) {
      console.error("Resume stream error:", error);
      setMessages(prev => [...prev, {
        role: "ai",
        content: "Error: Could not resume the query.",
        isError: true,
        error_code: "NETWORK_ERROR",
      }]);
      setPendingQuestions(null);
      setIsClarifying(false);
      setRequestId(null);
    } finally {
      setIsLoading(false);
      setCurrentNode("");
    }
  }, [threadId, selectedModel, selectedProvider, requestId]);

  const handleExport = useCallback(async (sql) => {
    if (!sql) return;
    try {
      const response = await api.post('/export-csv', { sql }, { responseType: 'blob' });
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
  }, []);

  const loadThread = useCallback(async (tid) => {
    try {
      const res = await api.get(`/threads/${tid}`);
      const msgs = (res.data.messages || []).map(m => ({
        role: m.role,
        content: m.content,
        data: m.data_results || null,
        tool_query: m.tool_query || null,
        nextStep: m.next_step || null,
        isError: m.isError || m.is_error || false,
        error_code: m.error_code || null,
      }));
      setMessages(msgs);
      setHistory(res.data.messages || []);
      setThreadId(tid);
      return msgs;
    } catch (error) {
      console.error("Failed to load thread:", error);
      return null;
    }
  }, []);

  const resetChat = useCallback(() => {
    setMessages([]);
    setHistory([]);
    setThreadId(`session_${Math.random().toString(36).slice(2, 11)}`);
    setPendingQuestions(null);
    setIsClarifying(false);
    setRequestId(null);
    resetStreaming();
  }, []);

  return {
    messages,
    setMessages,
    history,
    setHistory,
    threadId,
    isLoading,
    streamingContent,
    currentNode,
    pendingQuestions,
    isClarifying,
    requestId,
    handleSend,
    handleClarifySubmit,
    handleExport,
    loadThread,
    resetChat,
    setIsClarifying,
  };
}
