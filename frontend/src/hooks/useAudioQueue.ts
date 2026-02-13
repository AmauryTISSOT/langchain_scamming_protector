import { useCallback, useRef, useState } from "react";
import type { Segment } from "../types";

function base64ToBlob(base64: string, mime = "audio/mpeg"): Blob {
  const bytes = atob(base64);
  const buffer = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) {
    buffer[i] = bytes.charCodeAt(i);
  }
  return new Blob([buffer], { type: mime });
}

export function useAudioQueue() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(-1);

  const play = useCallback(async (segments: Segment[]) => {
    setIsPlaying(true);

    for (let i = 0; i < segments.length; i++) {
      setCurrentIndex(i);
      const seg = segments[i];

      if (seg.type === "pause") {
        await new Promise((r) => setTimeout(r, (seg.duration ?? 1.5) * 1000));
      } else if (seg.type === "sound" && seg.sound_file) {
        await playUrl(`http://localhost:8000${seg.sound_file}`);
      } else if (seg.type === "text" && seg.tts_audio) {
        const blob = base64ToBlob(seg.tts_audio);
        const url = URL.createObjectURL(blob);
        try {
          await playUrl(url);
        } finally {
          URL.revokeObjectURL(url);
        }
      }
    }

    setCurrentIndex(-1);
    setIsPlaying(false);
  }, []);

  async function playUrl(url: string): Promise<void> {
    return new Promise((resolve) => {
      if (!audioRef.current) {
        audioRef.current = new Audio();
      }
      const audio = audioRef.current;
      audio.src = url;
      audio.onended = () => resolve();
      audio.onerror = () => resolve();
      audio.play().catch(() => resolve());
    });
  }

  return { play, isPlaying, currentIndex, audioRef };
}
