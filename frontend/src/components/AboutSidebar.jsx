const GITHUB_URL = "https://github.com/GhaidaAL36/ARJdetector";
const CONTACT_EMAIL = "arjdetect@gmail.com";

function ContactLink({ href, label, icon }) {
  const external = href.startsWith("http");

  return (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noreferrer" : undefined}
      aria-label={label}
      title={label}
      className="grid h-10 w-10 place-items-center rounded-lg border border-line bg-surface text-base text-muted transition-colors hover:border-ink/30 hover:bg-canvas hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
    >
      <i className={icon} aria-hidden="true"></i>
    </a>
  );
}

export default function AboutSidebar() {
  return (
    <aside className="flex w-72 shrink-0 flex-col justify-between border-s border-line bg-sidebar px-6 py-7">
      <div>
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-ink text-lg font-bold text-surface">
            ع
          </span>
          <div className="leading-tight">
            <p className="text-lg font-bold tracking-wide">ARJ</p>
            <p className="text-xs text-muted">كاشف العَرَنجيّة</p>
          </div>
        </div>

        {/* will change */}
        <p className="mt-7 text-xs leading-6 text-muted">
          تعمل الأداة عن طريق قواعد لغويّة متّبعة، ترصد التراكيب المنقولة عن
          الإنجليزية في النص العربي، وتقترح بدائل أقرب إلى أساليب العربية.
        </p>

        <div className="mt-8">
          <p className="mb-3 text-xs text-muted">تواصل</p>
          <div className="flex gap-2">
            <ContactLink
              href={GITHUB_URL}
              label="مستودع المشروع على GitHub"
              icon="fa-brands fa-github"
            />
            <ContactLink
              href={`mailto:${CONTACT_EMAIL}`}
              label="راسلنا بالبريد الإلكتروني"
              icon="fa-solid fa-envelope"
            />
          </div>
        </div>
      </div>

      <p className="text-[11px] text-muted">
        نسخة تجريبية · القواعد قيد التوسعة
      </p>
    </aside>
  );
}
