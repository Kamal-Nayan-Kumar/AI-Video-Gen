/**
 * Shows which providers are actually configured.
 *
 * In demo mode every stage still runs, but content, narration and imagery come
 * from local fallbacks rather than a paid API — worth stating plainly rather
 * than letting the UI imply a model call happened.
 */
export default function ModeBadge({ health }) {
  const { loading, online, mode, capabilities } = health;

  if (loading) return <span className="tag">checking backend…</span>;

  if (!online) {
    return (
      <span className="tag tag--bad">
        <span className="dot" />
        backend offline
      </span>
    );
  }

  const live = mode === "live";

  return (
    <span className="tag" title="Provider status reported by /health">
      <span className="dot" style={{ color: live ? "var(--good)" : "var(--warn)" }} />
      {live ? (capabilities?.provider === "groq" ? "groq" : "live") : "demo mode"}
      {capabilities && (
        <span className="tag__detail">
          {[
            capabilities.content && "AI",
            capabilities.voice && "TTS",
            capabilities.images && "photos",
          ]
            .filter(Boolean)
            .join(" · ") || "local fallbacks"}
        </span>
      )}
    </span>
  );
}