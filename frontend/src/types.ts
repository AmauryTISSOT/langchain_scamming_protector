export interface Segment {
  type: "text" | "sound" | "pause";
  content?: string;
  sound_tag?: string;
  sound_file?: string;
  tts_audio?: string;
  duration?: number;
}

export interface ChatResponse {
  session_id: string;
  segments: Segment[];
  raw_text: string;
}

export interface ChatMessage {
  id: string;
  role: "scammer" | "jeanne";
  text: string;
  segments?: Segment[];
}
