export async function analyzeText(text) {
  const response = await fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`analyze failed with ${response.status}`);
  }

  return response.json();
}
