import { useState } from "react";

function SuggestionCard({ index, phrase, suggestion, open, onToggle }) {
  return (
    <article className="rounded-xl border border-line bg-sidebar p-4">
      <div className="flex items-start justify-between gap-3">
        <span className="rounded-md bg-flag-soft px-2 py-0.5 text-sm font-medium text-flag">
          {phrase}
        </span>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={open}
            aria-label={open ? "إخفاء الاقتراح" : "إظهار الاقتراح"}
            className="grid h-5 w-5 place-items-center text-xs text-muted transition-transform hover:text-ink lg:hidden"
          >
            <i
              className={`fa-solid fa-chevron-down ${open ? "rotate-180" : ""}`}
              aria-hidden="true"
            ></i>
          </button>
          <span className="grid h-5 w-5 place-items-center rounded-md bg-flag text-[11px] font-bold text-surface">
            {index}
          </span>
        </div>
      </div>
      <p
        className={`mt-3 text-xs leading-6 text-muted lg:block ${open ? "block" : "hidden"}`}
      >
        {suggestion}
      </p>
    </article>
  );
}

const TOGGLE =
  "grid h-7 w-7 place-items-center rounded-lg text-sm text-muted transition-colors hover:bg-canvas hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink";

function CountBadge({ count }) {
  return (
    <span className="grid h-5 w-5 place-items-center rounded-full bg-flag text-[11px] font-bold text-surface">
      {count}
    </span>
  );
}

export default function SuggestionsPanel({
  matches = [],
  collapsed = false,
  onToggle,
  className = "",
}) {
  const [openIndex, setOpenIndex] = useState(0);
  const [shown, setShown] = useState(matches);

  if (shown !== matches) {
    setShown(matches);
    setOpenIndex(0);
  }

  if (collapsed) {
    return (
      <aside
        className={`flex w-full shrink-0 items-center gap-3 border-line bg-sidebar px-6 py-3 lg:w-14 lg:flex-col lg:border-e lg:px-0 lg:py-7 ${className}`}
      >
        <button
          type="button"
          onClick={onToggle}
          aria-label="إظهار الاقتراحات"
          title="إظهار الاقتراحات"
          className={TOGGLE}
        >
          <i className="fa-solid fa-list-ul" aria-hidden="true"></i>
        </button>
        {matches.length > 0 && <CountBadge count={matches.length} />}
      </aside>
    );
  }

  return (
    <aside
      className={`flex w-full shrink-0 flex-col border-line bg-sidebar px-6 py-7 lg:w-80 lg:border-e ${className}`}
    >
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-bold">الاقتراحات</h2>
          {matches.length > 0 && <CountBadge count={matches.length} />}
        </div>
        <button
          type="button"
          onClick={onToggle}
          aria-label="إخفاء الاقتراحات"
          title="إخفاء الاقتراحات"
          className={`${TOGGLE} hidden lg:grid`}
        >
          <i className="fa-solid fa-xmark" aria-hidden="true"></i>
        </button>
      </div>

      {matches.length === 0 ? (
        <p className="text-xs leading-6 text-muted">
          لم يُعثر على ملاحظات أسلوبية في هذا النص.
        </p>
      ) : (
        <div className="flex flex-col gap-3 lg:min-h-0 lg:flex-1 lg:overflow-y-auto">
          {matches.map((match, position) => (
            <SuggestionCard
              key={`${match.flagged_phrase}-${position}`}
              index={position + 1}
              phrase={match.flagged_phrase}
              suggestion={match.suggestion}
              open={openIndex === position}
              onToggle={() =>
                setOpenIndex(openIndex === position ? -1 : position)
              }
            />
          ))}
        </div>
      )}
    </aside>
  );
}
