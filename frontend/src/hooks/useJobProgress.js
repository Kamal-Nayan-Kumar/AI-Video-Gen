import { useEffect, useState } from "react";

const MAX_EVENTS = 200;

/**
 * Subscribe to a job's server-sent event stream.
 *
 * The stream is the only channel the UI has for progress, so the hook is
 * deliberately defensive:
 *
 *  - a snapshot of the current state arrives on connect, so a client that
 *    attaches late renders the right bar immediately;
 *  - every event carries `stage` and `elapsed`, so the UI never has to guess;
 *  - the backend emits comment frames as keep-alives, which `EventSource`
 *    ignores, so a long encode does not look like a dropped connection;
 *  - a transient error is retried, but a stream that the server has closed
 *    for good is not reopened in a loop.
 */
export function useJobProgress(jobId) {
  const [events, setEvents] = useState([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const [stage, setStage] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!jobId) {
      setEvents([]);
      setProgress(0);
      setStatus("idle");
      setMessage("");
      setStage(null);
      setElapsed(0);
      setConnected(false);
      return;
    }

    setEvents([]);
    setProgress(0);
    setStatus("running");
    setMessage("Opening the progress stream…");
    setStage(null);
    setElapsed(0);

    const base = import.meta.env.VITE_API_BASE ?? "";
    const source = new EventSource(`${base}/api/progress/${jobId}`);

    source.onopen = () => setConnected(true);

    source.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }

      setConnected(true);
      setProgress(payload.progress ?? 0);
      setStatus(payload.status ?? "running");
      setMessage(payload.message ?? "");
      if (payload.stage) setStage(payload.stage);
      if (typeof payload.elapsed === "number") setElapsed(payload.elapsed);

      setEvents((previous) => {
        const row = {
          stage: payload.stage ?? null,
          message: payload.message ?? "",
          progress: payload.progress ?? 0,
          timestamp: payload.timestamp ?? "",
        };
        const last = previous[previous.length - 1];

        // The opening snapshot can repeat the current state; skip duplicates so
        // the log does not fill with the same line.
        if (last?.message === row.message && last?.progress === row.progress) {
          return previous;
        }

        // Encode ticks several times a second. Replace the last row instead of
        // appending, so the log stays readable and the newest frame is visible.
        if (payload.coalesce && last) {
          return [...previous.slice(0, -1), row];
        }

        return [...previous, row].slice(-MAX_EVENTS);
      });

      if (payload.done || payload.status === "completed" || payload.status === "error") {
        source.close();
        setConnected(false);
      }
    };

    source.onerror = () => {
      setConnected(false);
      // EventSource reconnects by itself unless it has been closed. A closed
      // stream means the job finished or was never accepted, so stop here
      // rather than reconnecting forever.
      if (source.readyState === EventSource.CLOSED) source.close();
    };

    return () => {
      source.close();
      setConnected(false);
    };
  }, [jobId]);

  return { events, progress, status, message, stage, elapsed, connected };
}
