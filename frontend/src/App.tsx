import { useCallback, useEffect, useState } from "react";
import { createSession, sendMessage } from "./api";
import type { ChatMessage } from "./types";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";
import { useAudioQueue } from "./hooks/useAudioQueue";

let msgId = 0;

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { play, isPlaying } = useAudioQueue();

  useEffect(() => {
    createSession().then(setSessionId).catch(console.error);
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      if (!sessionId || isLoading) return;

      const scammerMsg: ChatMessage = {
        id: String(++msgId),
        role: "scammer",
        text,
      };
      setMessages((prev) => [...prev, scammerMsg]);
      setIsLoading(true);

      try {
        const res = await sendMessage(sessionId, text);
        const jeanneMsg: ChatMessage = {
          id: String(++msgId),
          role: "jeanne",
          text: res.raw_text,
          segments: res.segments,
        };
        setMessages((prev) => [...prev, jeanneMsg]);
        play(res.segments);
      } catch (err) {
        console.error(err);
        const errorMsg: ChatMessage = {
          id: String(++msgId),
          role: "jeanne",
          text: "Oh la la, je n'entends plus rien... La ligne est mauvaise !",
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading, play]
  );

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-6 py-4 shadow-sm">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              Jeanne vs Arnaqueur
            </h1>
            <p className="text-xs text-gray-500">
              Simulation interactive d'arnaque telephonique
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isPlaying && (
              <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Audio en cours
              </span>
            )}
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                sessionId ? "bg-emerald-500" : "bg-gray-300"
              }`}
              title={sessionId ? "Connecte" : "Connexion..."}
            />
          </div>
        </div>
      </header>

      {/* Chat area */}
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col overflow-hidden">
        <ChatWindow messages={messages} isLoading={isLoading} />
        <InputBar onSend={handleSend} disabled={!sessionId || isLoading} />
      </div>
    </div>
  );
}
