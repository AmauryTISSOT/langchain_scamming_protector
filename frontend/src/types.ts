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

export interface AutoStartResponse {
  session_id: string;
  scammer_segments: Segment[];
  scammer_text: string;
}

export interface DirectorInfo {
  scam_type: string;
  stage: string;
  stage_description: string;
  objective_used: string;
}

export interface InterventionRequired {
  message: string;
  choices: string[];
}

export interface AutoTurnResponse {
  session_id: string;
  turn_number: number;
  victim_segments: Segment[];
  victim_text: string;
  scammer_segments: Segment[];
  scammer_text: string;
  director_info?: DirectorInfo;
  is_complete: boolean;
  intervention_required?: InterventionRequired;
}
