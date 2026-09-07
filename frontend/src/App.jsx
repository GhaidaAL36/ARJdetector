import { useState } from "react";
import AboutSidebar from "./components/AboutSidebar";
import SuggestionsPanel from "./components/SuggestionsPanel";
import TextSection from "./components/TextSection";

const PLACEHOLDER_MATCHES = [
  {
    rule: "تم",
    flagged_phrase: "تم إطلاق",
    explanation: "مبني للمجهول مُعرَّب",
    suggestion: "يمكن استبدال «تم» بفعل مبني للمجهول مباشرة",
    spans: [{ start: 0, end: 8 }],
  },
  {
    rule: "بشكل",
    flagged_phrase: "بشكل رسمي",
    explanation: "حشو أسلوبي",
    suggestion: "يمكن حذف «بشكل» أو استبدالها بصياغة أكثر طبيعية",
    spans: [{ start: 24, end: 33 }],
  },
  {
    rule: "قام بـ",
    flagged_phrase: "قام بإجراء",
    explanation: "فعل مساعد زائد",
    suggestion: "يمكن استبدال «قام بـ» بالفعل المباشر",
    spans: [
      { start: 42, end: 45 },
      { start: 53, end: 59 },
    ],
  },
];

export default function App() {
  const [text, setText] = useState("");

  return (
    <div className="flex h-screen">
      <SuggestionsPanel matches={PLACEHOLDER_MATCHES} />
      <TextSection value={text} onChange={setText} matchCount={PLACEHOLDER_MATCHES.length} />
      <AboutSidebar />
    </div>
  );
}
