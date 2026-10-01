import { useCallback, useEffect, useState } from "react";

import Composer from "./components/Composer";
import ProgressPanel from "./components/ProgressPanel";
import Player from "./components/Player";
import ModeBadge from "./components/ModeBadge";
import { useCapabilities } from "./hooks/useCapabilities";
import { useJobProgress } from "./hooks/useJobProgress";
import { createGeneration, getJob } from "./utils/api";

export default function App() {
  const health = useCapabilities();
  const progress = useJobProgress();

  const [jobId, setJobId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const running = submitting || (progress.status === "running" && !result);

  const submit = useCallback(
    async (settings) => {
      setError(null);
      setResult(null);
      setSubmitting(true);
      setJobId(null);

      try {
        const { job_id } = await createGeneration(settings);
        setJobId(job_id);
      } catch (cause) {
        setError(cause.message);
        setSubmitting(false);
        return;
      }

      // The SSE stream reports completion; fetch the payload once it lands.
      setSubmitting(false);
    },
    []
  );

  // Pull the finished job as soon as the stream reports it is done.
  useEffect(() => {
    if (!jobId || result || error) return;
    if (progress.status !== "completed" && progress.status !== "error") return;

    if (progress.status === "error") {
      setError(progress.message.replace(/^Failed:\s*/, "") || "Generation failed");
      setJobId(null);
      return;
    }

    let cancelled = false;
    getJob(jobId)
      .then((data) => {
        if (!cancelled) setResult({ ...data, jobId });
      })
      .catch((cause) => {
        if (!cancelled) setError(cause.message);
      })
      .finally(() => {
        if (!cancelled) setJobId(null);
      });

    return () => {
      cancelled = true;
    };
  }, [jobId, result, error, progress.status, progress.message]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setJobId(null);
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
                connected={progress.connected}
                error={error}
                hasRun={Boolean(jobId) || progress.events.length > 0}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}