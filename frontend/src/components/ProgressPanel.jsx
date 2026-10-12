import { useEffect, useRef } from "react";

/** The pipeline stages, in order. Matches STAGES in backend/app.py. */
const STAGES = [
  { id: "outline", label: "Outline from topic" },
  { id: "script", label: "Narration script" },
  { id: "voice", label: "Voice synthesis" },
  { id: "visuals", label: "Slide layout and visuals" },
  { id: "encode", label: "Encode final MP4" },
];

function formatElapsed(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

/**
 * Live job progress.
 *
 * The log is a scrolling list rather than a spinner, because a five-stage
 * pipeline is worth watching: it shows which stage is slow. Stages advance
 * from the `stage` field on each SSE event, so the marks reflect what the
 * backend is actually doing rather than a guessed percentage.
 */
export default function ProgressPanel({
  running,
  events,
  progress,
  status,
  message,
  stage,
  elapsed,
  connected,
  error,
  hasRun,
}) {
  const logRef = useRef(null);

  useEffect(() => {
    const node = logRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [events.length]);

  // Before a run, show the plan rather than an empty box.
  if (!hasRun && !running) {
    return (
      <aside className="rail">
        <div className="rail__head">
          <h2 className="rail__title">What happens next</h2>
        </div>
        <ol className="stages">
          {STAGES.map((item, index) => (
            <li key={item.id} className="stages__item">
              <span className="stages__index num">{index + 1}</span>
              <span>{item.label}</span>
            </li>
          ))}
        </ol>
        <p className="rail__note">
          Progress arrives here live while the video builds. A five-slide deck
          usually takes 40 to 90 seconds.
        </p>
      </aside>
    );
  }

  const failed = status === "error" || Boolean(error);
  const done = status === "completed";
  const currentIndex = STAGES.findIndex((item) => item.id === stage);

  return (
    <aside className="rail">
      <div className="rail__head">
        <h2 className="rail__title">
          {failed ? "Generation failed" : done ? "Deck ready" : "Building your deck"}
        </h2>
        <span
          className={`tag ${failed ? "tag--bad" : done ? "tag--good" : "tag--accent"}`}
        >
          <span className="dot" />
          {failed ? "error" : done ? "complete" : connected ? "live" : "connecting"}
        </span>
      </div>

      <div className="meter__row">
        <span className="meter__pct num">{progress}%</span>
        <span className="meter__elapsed num">{formatElapsed(elapsed)}</span>
      </div>

      <div
        className="meter"
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={`${progress}%, ${message}`}
      >
        <div
          className={`meter__fill ${failed ? "meter__fill--bad" : done ? "meter__fill--done" : ""}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <p className="rail__status">{message || "Waiting for the first update…"}</p>

      <ol className="stages">
        {STAGES.map((item, index) => {
          // Done once a later stage has started; the current one is active.
          const isDone = currentIndex > index || done;
          const isActive = currentIndex === index && !done && !failed;
          const className = [
            "stages__item",
            isDone ? "stages__item--done" : "",
            isActive ? "stages__item--active" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <li key={item.id} className={className}>
              <span className="stages__index num">{index + 1}</span>
              <span>{item.label}</span>
            </li>
          );
        })}
      </ol>

      {error ? <p className="rail__error">{error}</p> : null}

      <div className="log" ref={logRef}>
        {events.map((event, index) => (
          <div key={`${event.timestamp}-${index}`} className="log__row">
            <span className="log__time num">{event.timestamp}</span>
            <span className="log__msg">{event.message}</span>
          </div>
        ))}
        {running && connected ? (
          <div className="log__row log__row--live">
            <span className="log__time num" />
            <span className="log__msg">streaming</span>
          </div>
        ) : null}
      </div>
    </aside>
  );
}
