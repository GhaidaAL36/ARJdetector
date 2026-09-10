import { useState } from "react";
import AboutSidebar from "./components/AboutSidebar";
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
    <div className="flex h-screen">
      {analyzed && (
        <SuggestionsPanel
          matches={matches}
          collapsed={!showSuggestions}
          onToggle={() => setShowSuggestions((shown) => !shown)}
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
      />
      <AboutSidebar />
    </div>
  );
}
