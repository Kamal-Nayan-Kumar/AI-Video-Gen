import { useEffect, useRef, useState } from "react";

/**
 * Subscribe to a job's server-sent event stream.
 *
 * The connection is torn down as soon as the backend reports `done`, and the
 * returned log is capped so a long-running job cannot grow without bound.
 */
export function useJobProgress(jobId) {
  const [events, setEvents] = useState([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef(null);

  useEffect(() => {
    if (!jobId) {
      setEvents([]);
      setProgress(0);
      setStatus("idle");
      setMessage("");
      setConnected(false);
      return;
    }

    setEvents([]);
    setProgress(0);
    setStatus("running");

    const base = import.meta.env.VITE_API_BASE ?? "";
    const source = new EventSource(`${base}/api/progress/${jobId}`);
    sourceRef.current = source;

    source.onopen = () => setConnected(true);

    source.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }

      setProgress(payload.progress ?? 0);
      setStatus(payload.status ?? "running");
      setMessage(payload.message ?? "");

      setEvents((previous) => {
        const last = previous[previous.length - 1];
        // The backend re-sends the current state as a heartbeat; skip repeats.
        if (last?.message === payload.message) return previous;
        return [
          ...previous,
          {
            message: payload.message ?? "",
            progress: payload.progress ?? 0,
            timestamp: payload.timestamp ?? "",
          },
        ].slice(-200);
      });

      if (payload.done || payload.status === "completed" || payload.status === "error") {
        source.close();
        setConnected(false);
      }
    };

    source.onerror = () => {
      setConnected(false);
      // EventSource reconnects on its own unless it has been closed, so only
      // tear down once the stream is genuinely finished.
      if (source.readyState === EventSource.CLOSED) source.close();
    };

    return () => {
      source.close();
      setConnected(false);
    };
  }, [jobId]);

  return { events, progress, status, message, connected };
}