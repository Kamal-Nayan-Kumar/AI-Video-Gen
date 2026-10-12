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
  const providers = Array.isArray(capabilities?.llm_providers)
    ? capabilities.llm_providers
    : [];

  // Every configured capability, so the badge is honest about what is live.
  const parts = [
    ...providers,
    capabilities?.voice && "TTS",
    capabilities?.images && "photos",
  ].filter(Boolean);

  return (
    <span className="tag" title="Provider status reported by /health">
      <span className="dot" style={{ color: live ? "var(--good)" : "var(--warn)" }} />
      {live ? "live" : "demo"}
      {parts.length > 0 && <span className="tag__detail">{parts.join(" + ")}</span>}
    </span>
  );
}
