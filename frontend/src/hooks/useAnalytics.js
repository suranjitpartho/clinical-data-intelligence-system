import { useState, useCallback, useEffect } from 'react';
import api from '../utils/api';
import { aggregateByRequestId, groupBySession } from '../utils/analytics-utils';

export function useAnalytics(currentView, analyticsSubView) {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [operationalData, setOperationalData] = useState(null);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(false);
  const [analyticsRange, setAnalyticsRange] = useState(7);
  const [analyticsPage, setAnalyticsPage] = useState(1);
  const [analyticsPageSize] = useState(10);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);

  const fetchAnalytics = useCallback(async (days = analyticsRange, page = analyticsPage, pageSize = analyticsPageSize) => {
    setIsAnalyticsLoading(true);
    try {
      const res = await api.get('/analytics', {
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
  }, [analyticsRange, analyticsPage, analyticsPageSize]);

  const fetchOperationalAnalytics = useCallback(async (days = analyticsRange) => {
    setIsAnalyticsLoading(true);
    try {
      const res = await api.get('/analytics/operational', {
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
  }, [analyticsRange]);

  const handleSyncAnalytics = useCallback(async () => {
    setIsSyncing(true);
    setSyncStatus("syncing");
    try {
      await api.post('/analytics/sync', null, {
        params: { days: analyticsRange }
      });

      setSyncStatus("polling");
      let found = false;
      for (let attempt = 1; attempt <= 12; attempt++) {
        await new Promise(r => setTimeout(r, 3000));
        try {
          const res = await api.get('/analytics', {
            params: { days: analyticsRange, page: 1, page_size: analyticsPageSize }
          });
          if (res.data?.recent_traces?.length > 0) {
            setAnalyticsData(res.data);
            found = true;
            setSyncStatus("complete");
            break;
          }
        } catch (_) { /* retry on error */ }
        setSyncStatus(`polling_${attempt}`);
      }
      if (!found) setSyncStatus("timeout");

      await Promise.all([
        fetchAnalytics(analyticsRange, 1, analyticsPageSize),
        fetchOperationalAnalytics(analyticsRange)
      ]);
    } catch (error) {
      console.error("Sync error:", error);
      setSyncStatus("timeout");
      alert("Intelligence sync failed. Verify Langfuse connectivity.");
    } finally {
      setIsSyncing(false);
    }
  }, [analyticsRange, analyticsPageSize, fetchAnalytics, fetchOperationalAnalytics]);

  const handleRangeChange = useCallback((days) => {
    setAnalyticsRange(days);
    setAnalyticsPage(1);
  }, []);

  // Refetch when range or page changes
  useEffect(() => {
    if (currentView === 'analytics') {
      if (analyticsSubView === 'traces') {
        fetchAnalytics(analyticsRange, analyticsPage, analyticsPageSize);
      } else {
        fetchOperationalAnalytics(analyticsRange);
      }
    }
  }, [currentView, analyticsRange, analyticsPage, analyticsSubView, fetchAnalytics, fetchOperationalAnalytics, analyticsPageSize]);

  return {
    analyticsData,
    operationalData,
    isAnalyticsLoading,
    analyticsRange,
    analyticsPage,
    analyticsPageSize,
    isSyncing,
    syncStatus,
    fetchAnalytics,
    fetchOperationalAnalytics,
    handleSyncAnalytics,
    handleRangeChange,
    setAnalyticsPage,
  };
}
