import { useEffect, useState } from "react";

const GITHUB_URL = "https://github.com/GhaidaAL36";
const CONTACT_EMAIL = "arjdetect@gmail.com";

const ICON =
  "grid h-8 w-8 place-items-center rounded-lg text-base text-muted transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink";

function EmailButton() {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 1800);
    return () => clearTimeout(timer);
  }, [copied]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(CONTACT_EMAIL);
      setCopied(true);
    } catch {
      window.location.href = `mailto:${CONTACT_EMAIL}`;
    }
  }

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`نسخ البريد الإلكتروني ${CONTACT_EMAIL}`}
      title={CONTACT_EMAIL}
      className={ICON}
    >
      <i
        className={copied ? "fa-solid fa-check" : "fa-solid fa-envelope"}
        aria-hidden="true"
      ></i>
    </button>
  );
}

export default function AboutSidebar() {
  return (
    <aside className="flex w-72 shrink-0 flex-col justify-between border-s border-line bg-sidebar px-6 py-7">
      <div>
        <div className="flex items-center gap-3">
          <img src="/icon.svg" alt="" className="h-10 w-10 shrink-0" />
          <p className="text-lg font-bold tracking-wide">إيجاز</p>
        </div>

        <p className="mt-7 text-xs leading-6 text-muted">
          تعمل الأداة بقواعد لغوية، تحدد التراكيب المنقولة عن الإنجليزية في النص
          العربي، وتقترح ما يمكن تغييره ليصبح الأسلوب أقرب إلى العربية.
        </p>

        <div className="mt-8">
          <p className="mb-2 text-xs text-muted">تواصل</p>
          <EmailButton />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-[11px] text-muted">
          نسخة تجريبية · القواعد قيد التوسعة
        </p>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noreferrer"
          aria-label="مستودع المشروع على GitHub"
          title="مستودع المشروع على GitHub"
          className={ICON}
        >
          <i className="fa-brands fa-github" aria-hidden="true"></i>
        </a>
      </div>
    </aside>
  );
}
