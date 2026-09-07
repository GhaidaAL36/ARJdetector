function arabicNumber(value) {
  return value.toLocaleString("ar-EG", { useGrouping: false });
}

function countWords(text) {
  const trimmed = text.trim();
  return trimmed === "" ? 0 : trimmed.split(/\s+/).length;
}

function notesLabel(count) {
  if (count === 1) return "ملاحظة أسلوبية واحدة";
  if (count === 2) return "ملاحظتان أسلوبيتان";
  if (count <= 10) return `${arabicNumber(count)} ملاحظات أسلوبية`;
  return `${arabicNumber(count)} ملاحظة أسلوبية`;
}

export default function TextSection({
  value,
  onChange,
  onAnalyze,
  matchCount = 0,
  analyzing = false,
}) {
  const words = countWords(value);
  const empty = words === 0;

  return (
    <section className="flex flex-1 flex-col bg-canvas px-8 py-7">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <h1 className="text-base font-bold">النص</h1>
          <span className="text-xs text-muted">
            {arabicNumber(words)} كلمة
          </span>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onChange("")}
            disabled={empty}
            className="rounded-lg border border-line bg-canvas px-4 py-1.5 text-sm text-ink transition-colors hover:border-ink/30 hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
          >
            مسح
          </button>
          <button
            type="button"
            onClick={onAnalyze}
            disabled={empty || analyzing}
            className="rounded-lg bg-ink px-5 py-1.5 text-sm text-surface transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
          >
            {analyzing ? "جارٍ التحليل…" : "تحليل"}
          </button>
        </div>
      </div>

      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="الصق النص العربي هنا…"
        spellCheck="false"
        aria-label="النص المراد تحليله"
        className="min-h-0 flex-1 resize-none rounded-xl border border-line bg-surface p-5 text-sm leading-8 text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
      />

      <div className="mt-3 flex h-5 items-center gap-2 text-xs text-muted">
        {matchCount > 0 && (
          <>
            <span className="h-1.5 w-1.5 rounded-full bg-flag" />
            <span>
              {notesLabel(matchCount)} في {arabicNumber(words)} كلمة
            </span>
          </>
        )}
      </div>
    </section>
  );
}
