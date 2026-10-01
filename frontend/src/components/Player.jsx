import { useEffect, useMemo, useRef, useState } from "react";

import { videoUrl } from "../utils/api";

function formatTime(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** Player with a chapter list that follows playback. */
export default function Player({ result }) {
  const { content_data: content, script_data: script, video_filename: filename, counts } = result;
  const videoRef = useRef(null);
  const [active, setActive] = useState(0);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  const chapters = useMemo(
    () =>
      (script?.slide_scripts ?? []).map((entry) => ({
        number: entry.slide_number,
        start: entry.start_time,
        end: entry.end_time,
        title:
          content?.slides?.find((s) => s.slide_number === entry.slide_number)?.title ??
          `Slide ${entry.slide_number}`,
      })),
    [script, content]
  );

  // Track which chapter is on screen as the video plays.
  useEffect(() => {
    const index = chapters.findIndex(
      (chapter) => current >= chapter.start && current < chapter.end
    );
    setActive(index === -1 ? Math.max(0, chapters.length - 1) : index);
  }, [current, chapters]);

  function seek(time) {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = time;
    video.play().catch(() => {
      /* autoplay may be blocked; the user can press play */
    });
  }

  const src = filename ? videoUrl(filename) : null;

  return (
    <div className="player">
      <div className="player__stage">
        {src ? (
          <video
            ref={videoRef}
            className="player__video"
            src={src}
            controls
            playsInline
            onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)}
            onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
          />
        ) : (
          <div className="player__empty">No video was produced.</div>
        )}

        <div className="player__meta">
          <div>
            <h1 className="player__title">{content?.topic}</h1>
            <p className="player__sub">
              {content?.slides?.length ?? 0} slides ·{" "}
              {formatTime(script?.total_duration ?? duration)} narrated
            </p>
          </div>
          <div className="player__tags">
            {counts?.text ? <span className="tag">{counts.text} text</span> : null}
            {counts?.image ? <span className="tag">{counts.image} image</span> : null}
            {counts?.animation ? (
              <span className="tag tag--accent">{counts.animation} animated</span>
            ) : null}
            <a
              className="btn"
              href={src ?? "#"}
              download={filename ?? "deck.mp4"}
              aria-disabled={!src}
            >
              Download MP4
            </a>
          </div>
        </div>
      </div>

      <div className="player__chapters">
        <h2 className="rail__title">Chapters</h2>
        <ol className="chapters">
          {chapters.map((chapter, index) => (
            <li key={chapter.number}>
              <button
                type="button"
                className="chapter"
                aria-current={index === active}
                onClick={() => seek(chapter.start)}
              >
                <span className="chapter__time num">{formatTime(chapter.start)}</span>
                <span className="chapter__title">{chapter.title}</span>
              </button>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}