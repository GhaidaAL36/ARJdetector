function arabicNumber(value) {
  return value.toLocaleString("ar-EG", { useGrouping: false });
}

function SuggestionCard({ index, phrase, suggestion }) {
  return (
    <article className="rounded-xl border border-line bg-sidebar p-4">
      <div className="flex items-start justify-between gap-3">
        <span className="rounded-md bg-flag-soft px-2 py-0.5 text-sm font-medium text-flag">
          {phrase}
        </span>
        <span className="grid h-5 w-5 shrink-0 place-items-center rounded-md bg-flag text-[11px] font-bold text-surface">
          {arabicNumber(index)}
        </span>
      </div>
      <p className="mt-3 text-xs leading-6 text-muted">{suggestion}</p>
    </article>
  );
}

export default function SuggestionsPanel({ matches = [], analyzed = false }) {
  return (
    <aside className="flex w-80 shrink-0 flex-col border-e border-line bg-sidebar px-6 py-7">
      <div className="mb-5 flex items-center gap-2">
        <h2 className="text-base font-bold">الاقتراحات</h2>
        {matches.length > 0 && (
          <span className="grid h-5 w-5 place-items-center rounded-full bg-flag text-[11px] font-bold text-surface">
            {arabicNumber(matches.length)}
          </span>
        )}
      </div>

      {matches.length === 0 ? (
        <p className="text-xs leading-6 text-muted">
          {analyzed
            ? "لم يُعثر على ملاحظات أسلوبية في هذا النص."
            : "لا توجد ملاحظات بعد. اكتب نصًّا ثم اضغط «تحليل»."}
        </p>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
          {matches.map((match, position) => (
            <SuggestionCard
              key={`${match.flagged_phrase}-${position}`}
              index={position + 1}
              phrase={match.flagged_phrase}
              suggestion={match.suggestion}
            />
          ))}
        </div>
      )}
    </aside>
  );
}
