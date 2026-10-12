import { useCallback, useEffect, useRef, useState } from "react";

import Composer from "./components/Composer";
import ProgressPanel from "./components/ProgressPanel";
import Player from "./components/Player";
import ModeBadge from "./components/ModeBadge";
import { useCapabilities } from "./hooks/useCapabilities";
import { useJobProgress } from "./hooks/useJobProgress";
import { createGeneration, getJob } from "./utils/api";

export default function App() {
  const health = useCapabilities();

  const [jobId, setJobId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [hasRun, setHasRun] = useState(false);

  // The hook has to be given the job id. Passing nothing leaves it undefined,
  // the EventSource is never opened and no progress ever arrives.
  const progress = useJobProgress(jobId);

  const running = submitting || (progress.status === "running" && !result);

  const submit = useCallback(async (settings) => {
    setError(null);
    setResult(null);
    setHasRun(true);
    setSubmitting(true);
    setJobId(null);

    try {
      const { job_id } = await createGeneration(settings);
      setJobId(job_id);
    } catch (cause) {
      setError(cause.message);
    } finally {
      setSubmitting(false);
    }
  }, []);

  // Pull the finished job as soon as the stream reports it is done.
  const fetchingRef = useRef(null);
  useEffect(() => {
    if (!jobId || result || error) return;
    if (progress.status !== "completed" && progress.status !== "error") return;

    if (progress.status === "error") {
      setError(progress.message.replace(/^Failed:\s*/, "") || "Generation failed");
      setJobId(null);
      return;
    }

    // Guard against React 18 StrictMode double-invoking the effect.
    if (fetchingRef.current === jobId) return;
    fetchingRef.current = jobId;

    let cancelled = false;
    getJob(jobId)
      .then((data) => {
        if (!cancelled) setResult({ ...data, jobId });
      })
      .catch((cause) => {
        if (!cancelled) setError(cause.message);
      });

    return () => {
      cancelled = true;
    };
  }, [jobId, result, error, progress.status, progress.message]);

  // Safety net. The stream is the intended channel, but a proxy can drop an
  // idle connection during the two-minute encode. If the stream goes quiet
  // while still running, poll the job endpoint so the result is never stranded.
  useEffect(() => {
    if (!jobId || !hasRun) return;
    if (progress.status === "completed" || progress.status === "error") return;
    if (result || error) return;

    const timer = setInterval(() => {
      // Deliberately quiet: a 409 is the normal "still running" answer, and the
      // browser logs every failed fetch as a console error. Suppress the noise.
      fetch(`/api/job/${jobId}`)
        .then((response) => {
          if (!response.ok) return null;
          return response.json();
        })
        .then((data) => {
          if (data) setResult({ ...data, jobId });
        })
        .catch(() => {
          /* network blip; the next tick retries */
        });
    }, 10000);

    return () => clearInterval(timer);
  }, [jobId, hasRun, progress.status, result, error]);

  // Clear the job id only once the payload has landed, so tearing the stream
  // down early cannot strand the player without a result.
  useEffect(() => {
    if (result) setJobId(null);
  }, [result]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setJobId(null);
    setHasRun(false);
  }, []);

  return (
    <div className="shell">
      <header className="shell__bar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true" />
          <span className="brand__name">Deckframe</span>
          <span className="brand__sub">topic to narrated video</span>
        </div>
        <div className="shell__bar-right">
          <ModeBadge health={health} />
          {result && (
            <button className="btn btn--ghost" onClick={reset}>
              New deck
            </button>
          )}
        </div>
      </header>

      <main className="shell__main">
        {result ? (
          <Player result={result} />
        ) : (
          <div className="workspace">
            <div className="workspace__form">
              <Composer onSubmit={submit} disabled={running} error={error} />
            </div>
            <div className="workspace__rail">
              <ProgressPanel
                running={running}
                events={progress.events}
                progress={progress.progress}
                status={progress.status}
                message={progress.message}
                stage={progress.stage}
                elapsed={progress.elapsed}
                connected={progress.connected}
                error={error}
                hasRun={hasRun}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}