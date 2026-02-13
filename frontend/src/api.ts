import type { ChatResponse, AutoStartResponse, AutoTurnResponse } from "./types";

const API_BASE = "http://localhost:8000";

export async function createSession(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/sessions`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create session");
  const data = await res.json();
  return data.session_id;
}

export async function sendMessage(
  sessionId: string,
  userInput: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, user_input: userInput }),
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: "DELETE" });
}

export async function startAutoConversation(
  sessionId: string
): Promise<AutoStartResponse> {
  const res = await fetch(`${API_BASE}/api/auto-conversation/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error("Failed to start auto conversation");
  return res.json();
}

export async function getNextTurn(
  sessionId: string,
  userChoice?: string
): Promise<AutoTurnResponse> {
  const res = await fetch(`${API_BASE}/api/auto-conversation/next`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      user_choice: userChoice || null
    }),
  });
  if (!res.ok) throw new Error("Failed to get next turn");
  return res.json();
}

export async function stopAutoConversation(
  sessionId: string
): Promise<void> {
  await fetch(`${API_BASE}/api/auto-conversation/stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
}
