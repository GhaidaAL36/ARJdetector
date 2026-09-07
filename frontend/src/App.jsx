import { useState } from "react";
import AboutSidebar from "./components/AboutSidebar";
import TextSection from "./components/TextSection";

export default function App() {
  const [text, setText] = useState("");

  return (
    <div className="flex h-screen">
      <TextSection value={text} onChange={setText} />
      <AboutSidebar />
    </div>
  );
}
