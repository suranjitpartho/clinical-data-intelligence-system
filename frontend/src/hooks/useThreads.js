import { useState, useEffect } from 'react';
import api from '../utils/api';

export function useThreads(isAuthenticated) {
  const [threads, setThreads] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [threadsHasMore, setThreadsHasMore] = useState(false);

  const fetchThreads = async (page = 1) => {
    try {
      const res = await api.get('/threads', {
        params: { page, page_size: 25 }
      });
      const data = res.data || {};
      setThreads(data.threads || []);
      setThreadsHasMore(data.has_more || false);
      setCurrentPage(page);
    } catch (error) {
      console.error("Failed to fetch threads:", error);
    }
  };

  const goToPage = (page) => {
    if (page < 1) return;
    fetchThreads(page);
  };

  const selectThread = async (tid) => {
    try {
      const res = await api.get(`/threads/${tid}`);
      return {
        messages: (res.data.messages || []).map(m => ({
          role: m.role,
          content: m.content,
          data: m.data_results || null,
          tool_query: m.tool_query || null,
          nextStep: m.next_step || null,
          isError: m.isError || m.is_error || false,
          error_code: m.error_code || null,
        })),
        history: res.data.messages || [],
      };
    } catch (error) {
      console.error("Failed to load thread:", error);
      return null;
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchThreads();
    }
  }, [isAuthenticated]);

  return {
    threads,
    currentPage,
    threadsHasMore,
    fetchThreads,
    goToPage,
    selectThread,
  };
}
