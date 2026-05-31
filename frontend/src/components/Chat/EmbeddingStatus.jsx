import React, { useState, useEffect, useRef } from 'react';
import { API_BASE } from '../../utils/api';

const EmbeddingStatus = () => {
  const [status, setStatus] = useState(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    let pollTimer;

    const poll = async () => {
      if (!mountedRef.current) return;
      try {
        const res = await fetch(`${API_BASE}/api/embedding/status`);
        const data = await res.json();
        if (!mountedRef.current) return;
        setStatus(data);
        if (data.status === 'complete' || data.status === 'skipped') return;
      } catch {
        // server not ready yet
      }
      pollTimer = setTimeout(poll, 3000);
    };

    const startTimer = setTimeout(poll, 2000);

    return () => {
      mountedRef.current = false;
      clearTimeout(startTimer);
      clearTimeout(pollTimer);
    };
  }, []);

  if (status?.status === 'in_progress') {
    return (
      <span className="opacity-60 font-medium text-clinical-blue">
        Indexing notes... ({status.done}/{status.total})
      </span>
    );
  }

  return <span className="opacity-40 font-medium">Build v1.2.5 Stable</span>;
};

export default EmbeddingStatus;
