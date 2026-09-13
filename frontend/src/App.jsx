import { useState } from "react";
import AboutSidebar, {
  AboutText,
  Brand,
  ContactRow,
  MetaRow,
} from "./components/AboutSidebar";
import SuggestionsPanel from "./components/SuggestionsPanel";
import TextSection from "./components/TextSection";
import { analyzeText } from "./api";

export default function App() {
  const [text, setText] = useState("");
  const [matches, setMatches] = useState([]);
  const [analyzed, setAnalyzed] = useState(false);
  const [editing, setEditing] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);

  function handleChange(next) {
    setText(next);
    setError("");
  }

  function handleClear() {
    setText("");
    setMatches([]);
    setAnalyzed(false);
    setEditing(true);
    setError("");
    setShowSuggestions(true);
  }

  async function handleAnalyze() {
    setAnalyzing(true);
    setError("");
    try {
      const result = await analyzeText(text);
      setMatches(result.matches);
      setAnalyzed(true);
      setEditing(false);
    } catch {
      setError("تعذّر الاتصال بالخادم. تأكّد من تشغيله ثم أعد المحاولة.");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col lg:h-screen lg:flex-row">
      <header className="order-1 flex justify-center px-6 pt-7 lg:hidden">
        <Brand />
      </header>

      {analyzed && (
        <SuggestionsPanel
          matches={matches}
          collapsed={!showSuggestions}
          onToggle={() => setShowSuggestions((shown) => !shown)}
          className="order-3 lg:order-none"
        />
      )}

      <TextSection
        value={text}
        onChange={handleChange}
        onAnalyze={handleAnalyze}
        onEdit={() => setEditing(true)}
        onClear={handleClear}
        matches={matches}
        editing={editing}
        analyzing={analyzing}
        error={error}
        className="order-2 lg:order-none"
      />

      <AboutSidebar />

      <div className="order-4 flex flex-col gap-6 px-6 pb-8 lg:hidden">
        <AboutText />
        <ContactRow />
        <MetaRow />
      </div>
    </div>
  );
}
