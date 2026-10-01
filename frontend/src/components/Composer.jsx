import { useState } from "react";

const LANGUAGES = [
  { value: "english", label: "English" },
  { value: "hindi", label: "Hindi" },
  { value: "kannada", label: "Kannada" },
  { value: "telugu", label: "Telugu" },
  { value: "tamil", label: "Tamil" },
  { value: "bengali", label: "Bengali" },
  { value: "marathi", label: "Marathi" },
  { value: "french", label: "French" },
];

const TONES = [
  { value: "formal", label: "Formal" },
  { value: "casual", label: "Casual" },
  { value: "storytelling", label: "Storytelling" },
  { value: "enthusiastic", label: "Enthusiastic" },
];

const EXAMPLES = [
  "How a refrigerator works",
  "Photosynthesis in plants",
  "Why the sky is blue",
];

export default function Composer({ onSubmit, disabled }) {
  const [topic, setTopic] = useState("");
  const [numSlides, setNumSlides] = useState(5);
  const [language, setLanguage] = useState("english");
  const [tone, setTone] = useState("formal");
  const [touched, setTouched] = useState(false);

  const ready = topic.trim().length >= 2;

  function handleSubmit(event) {
    event.preventDefault();
    setTouched(true);
    if (!ready || disabled) return;
    onSubmit({ topic: topic.trim(), num_slides: numSlides, language, tone });
  }

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <div className="composer__intro">
        <h1 className="composer__title">
          Turn a topic into a narrated video deck
        </h1>
        <p className="composer__lede">
          Describe a subject and the pipeline drafts the outline, writes and
          synthesises the narration, lays out each slide, renders animations
          where they earn their place, and encodes the final MP4.
        </p>
      </div>

      <div className="field">
        <label className="label" htmlFor="topic">
          Topic
        </label>
        <input
          id="topic"
          className="input input--lg"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. How a refrigerator works"
          disabled={disabled}
          autoComplete="off"
          spellCheck="false"
        />
        <div className="composer__examples">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              className="chip"
              onClick={() => setTopic(example)}
              disabled={disabled}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      <div className="composer__grid">
        <div className="field">
          <span className="label" id="slides-label">
            Slides
          </span>
          <div className="segmented" role="group" aria-labelledby="slides-label">
            {[3, 5, 7, 9].map((count) => (
              <button
                key={count}
                type="button"
                className="segmented__item"
                aria-pressed={numSlides === count}
                onClick={() => setNumSlides(count)}
                disabled={disabled}
              >
                {count}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label className="label" htmlFor="language">
            Language
          </label>
          <select
            id="language"
            className="select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={disabled}
          >
            {LANGUAGES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="label" htmlFor="tone">
            Tone
          </label>
          <select
            id="tone"
            className="select"
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            disabled={disabled}
          >
            {TONES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {touched && !ready && <p className="composer__hint">Enter at least a couple of characters.</p>}

      <button
        type="submit"
        className="btn btn--primary btn--lg composer__submit"
        disabled={disabled || !ready}
      >
        {disabled ? (
          <>
            <Spinner /> Generating
          </>
        ) : (
          "Generate deck"
        )}
      </button>
    </form>
  );
}

function Spinner() {
  return (
    <svg className="spin" width="15" height="15" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" fill="none" opacity="0.25" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  );
}