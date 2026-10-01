import { useEffect, useRef } from "react";

/**
 * Live job progress.
 *
 * The log is a scrolling terminal-style list rather than a spinner, because a
 * five-stage pipeline is worth watching: it shows which stage is slow.
 */
export default function ProgressPanel({
  running,
  events,
  progress,
  status,
  message,
  connected,
  error,
  hasRun,
}) {
  const logRef = useRef(null);

  useEffect(() => {
    const node = logRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [events.length]);

  if (!hasRun && !running) {
    return (
      <aside className="rail">
        <div className="rail__head">
          <h2 className="rail__title">Pipeline</h2>
        </div>
        <ol className="stages">
          {STAGES.map((stage, index) => (
            <li key={stage} className="stages__item">
              <span className="stages__index num">{index + 1}</span>
              <span>{stage}</span>
            </li>
          ))}
        </ol>
        <p className="rail__note">
          Progress streams from the backend over server-sent events as each
          stage completes.
        </p>
      </aside>
    );
  }

  const failed = status === "error" || Boolean(error);

  return (
    <aside className="rail">
      <div className="rail__head">
        <h2 className="rail__title">
          {failed ? "Failed" : running ? "Working" : "Done"}
        </h2>
        <span className={`tag ${failed ? "tag--bad" : running ? "tag--accent" : "tag--good"}`}>
          <span className="dot" />
          {failed ? "error" : running ? `${progress}%` : "complete"}
        </span>
      </div>

      <div className="meter" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={`meter__fill ${failed ? "meter__fill--bad" : ""}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <p className="rail__status">{message || "Waiting for the first update…"}</p>

      <div className="log" ref={logRef}>
        {events.map((event, index) => (
          <div key={`${event.timestamp}-${index}`} className="log__row">
            <span className="log__time num">{event.timestamp}</span>
            <span className="log__msg">{event.message}</span>
          </div>
        ))}
        {running && connected && (
          <div className="log__row log__row--live">
            <span className="log__time num" />
            <span className="log__msg">streaming…</span>
          </div>
        )}
      </div>
    </aside>
  );
}

const STAGES = [
  "Outline from topic",
  "Narration script",
  "Voice synthesis",
  "Slide layout & visuals",
  "Encode final MP4",
];