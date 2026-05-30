import { API_BASE } from './api';

export async function parseSSEStream(apiUrl, body, handlers = {}) {
  const { onNodeStart, onToken, onDone, onClarify, onError } = handlers;

  const token = localStorage.getItem('token');
  const response = await fetch(`${API_BASE}${apiUrl}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(body),
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
        onNodeStart?.(data.node);
      } else if (event === "token") {
        onToken?.(data.content);
      } else if (event === "done") {
        onDone?.(data);
      } else if (event === "clarify") {
        onClarify?.(data);
        return 'clarified';
      } else if (event === "error") {
        onError?.(data);
      }
    }
  }
  return 'completed';
}
