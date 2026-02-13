import { useCallback, useEffect, useRef, useState } from "react";
import {
  createSession,
  startAutoConversation,
  getNextTurn,
  stopAutoConversation,
} from "./api";
import type { ChatMessage, Segment } from "./types";
import ChatWindow from "./components/ChatWindow";
import { useAudioQueue } from "./hooks/useAudioQueue";

let msgId = 0;

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [turnCount, setTurnCount] = useState(0);
  const [maxTurns] = useState(15);
  const { play, isPlaying } = useAudioQueue();
  const stoppedRef = useRef(false);

  useEffect(() => {
    createSession().then(setSessionId).catch(console.error);
  }, []);

  const addMessage = useCallback(
    (role: "scammer" | "jeanne", text: string, segments?: Segment[]) => {
      const msg: ChatMessage = {
        id: String(++msgId),
        role,
        text,
        segments,
      };
      setMessages((prev) => [...prev, msg]);
    },
    []
  );

  const playSegments = useCallback(
    async (segments: Segment[]) => {
      await play(segments);
    },
    [play]
  );

  const handleStart = useCallback(async () => {
    if (!sessionId || isRunning) return;

    stoppedRef.current = false;
    setIsRunning(true);
    setIsLoading(true);
    setMessages([]);
    setTurnCount(0);

    try {
      // 1. Start: scammer opening message
      const startRes = await startAutoConversation(sessionId);
      addMessage("scammer", startRes.scammer_text, startRes.scammer_segments);
      setIsLoading(false);

      // Play scammer audio
      await playSegments(startRes.scammer_segments);

      // 2. Loop turns
      let complete = false;
      while (!complete && !stoppedRef.current) {
        setIsLoading(true);
        const turnRes = await getNextTurn(sessionId);
        setTurnCount(turnRes.turn_number);
        setIsLoading(false);

        if (stoppedRef.current) break;

        // Show and play Jeanne's response
        addMessage("jeanne", turnRes.victim_text, turnRes.victim_segments);
        await playSegments(turnRes.victim_segments);

        if (stoppedRef.current) break;

        // Show and play scammer's response (if not complete)
        if (!turnRes.is_complete && turnRes.scammer_text) {
          addMessage(
            "scammer",
            turnRes.scammer_text,
            turnRes.scammer_segments
          );
          await playSegments(turnRes.scammer_segments);
        }

        complete = turnRes.is_complete;
      }
    } catch (err) {
      console.error(err);
      addMessage(
        "jeanne",
        "Oh la la, la ligne a coupé..."
      );
    } finally {
      setIsRunning(false);
      setIsLoading(false);
    }
  }, [sessionId, isRunning, addMessage, playSegments]);

  const handleStop = useCallback(async () => {
    if (!sessionId) return;
    stoppedRef.current = true;
    try {
      await stopAutoConversation(sessionId);
    } catch {
      // ignore
    }
    setIsRunning(false);
    setIsLoading(false);
  }, [sessionId]);

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
              Simulation automatique d'arnaque telephonique
            </p>
          </div>
          <div className="flex items-center gap-3">
            {isRunning && (
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                Tour {turnCount} / {maxTurns}
              </span>
            )}
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

        {/* Control panel */}
        <div className="border-t border-gray-200 bg-white px-4 py-3">
          <div className="flex items-center justify-center gap-3">
            {!isRunning ? (
              <button
                onClick={handleStart}
                disabled={!sessionId}
                className="rounded-xl bg-emerald-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Demarrer la conversation
              </button>
            ) : (
              <button
                onClick={handleStop}
                className="rounded-xl bg-red-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-red-600 transition-colors"
              >
                Arreter
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
