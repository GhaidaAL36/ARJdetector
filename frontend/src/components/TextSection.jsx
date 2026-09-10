import { useEffect, useRef } from "react";

function countWords(text) {
  const trimmed = text.trim();
  return trimmed === "" ? 0 : trimmed.split(/\s+/).length;
}

function notesLabel(count) {
  if (count === 1) return "ملاحظة أسلوبية واحدة";
  if (count === 2) return "ملاحظتان أسلوبيتان";
  if (count <= 10) return `${count} ملاحظات أسلوبية`;
  return `${count} ملاحظة أسلوبية`;
}

function buildSegments(text, matches) {
  const marks = [];
  matches.forEach((match, index) => {
    for (const span of match.spans) marks.push({ ...span, match: index });
  });
  marks.sort((a, b) => a.start - b.start);

  const segments = [];
  let cursor = 0;
  for (const mark of marks) {
    if (mark.end <= cursor) continue;
    const start = Math.max(mark.start, cursor);
    if (start > cursor) segments.push({ text: text.slice(cursor, start) });
    segments.push({ text: text.slice(start, mark.end), match: mark.match });
    cursor = mark.end;
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor) });

  return segments;
}

const BOX = "flex-1 min-h-0 overflow-y-auto rounded-xl border border-line bg-surface p-5 text-sm leading-8 text-ink";

export default function TextSection({
  value,
  onChange,
  onAnalyze,
  onEdit,
  onClear,
  matches = [],
  editing = true,
  analyzing = false,
  error = "",
}) {
  const words = countWords(value);
  const empty = words === 0;
  const highlighted = !editing && matches.length > 0;
  const textarea = useRef(null);

  useEffect(() => {
    if (!editing) return;
    const node = textarea.current;
    if (!node) return;
    node.focus();
    node.setSelectionRange(node.value.length, node.value.length);
  }, [editing]);

  return (
    <section className="flex flex-1 flex-col bg-canvas px-8 py-7">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <h1 className="text-base font-bold">نص تجريبي</h1>
          <span className="text-xs text-muted">{words} كلمة</span>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onClear}
            disabled={empty}
            className="rounded-lg border border-line bg-canvas px-4 py-1.5 text-sm text-ink transition-colors hover:border-ink/30 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
          >
            مسح
          </button>
          <button
            type="button"
            onClick={highlighted ? onEdit : onAnalyze}
            disabled={empty || analyzing}
            className="rounded-lg bg-ink px-5 py-1.5 text-sm text-surface transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
          >
            {analyzing ? "جارٍ التحليل…" : highlighted ? "تعديل" : "تحليل"}
          </button>
        </div>
      </div>

      {highlighted ? (
        <div
          onClick={onEdit}
          className={`${BOX} cursor-text whitespace-pre-wrap break-words`}
        >
          {buildSegments(value, matches).map((segment, index) =>
            segment.match === undefined ? (
              segment.text
            ) : (
              <mark
                key={index}
                className="rounded bg-flag-soft px-0.5 text-ink"
              >
                {segment.text}
                <sup className="ms-0.5 select-none text-[10px] font-bold text-flag">
                  {segment.match + 1}
                </sup>
              </mark>
            ),
          )}
        </div>
      ) : (
        <textarea
          ref={textarea}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="أكتب او ألصق النص هنا…"
          spellCheck="false"
          aria-label="النص المراد تحليله"
          className={`${BOX} resize-none placeholder:text-muted focus:outline-none`}
        />
      )}

      <div className="mt-3 flex h-5 items-center gap-2 text-xs">
        {error ? (
          <span className="text-flag">{error}</span>
        ) : (
          highlighted && (
            <>
              <span className="h-1.5 w-1.5 rounded-full bg-flag" />
              <span className="text-muted">
                {notesLabel(matches.length)} في {words} كلمة
              </span>
            </>
          )
        )}
      </div>
    </section>
  );
}
