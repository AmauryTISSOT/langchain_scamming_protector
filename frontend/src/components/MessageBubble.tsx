import type { ChatMessage, Segment } from "../types";

const SOUND_LABELS: Record<string, string> = {
  DOG_BARK: "Poupoune aboie",
  DOORBELL: "Sonnette",
  COUGHING_FIT: "Quinte de toux",
};

function SegmentBadge({ segment }: { segment: Segment }) {
  if (segment.type === "sound") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
        <span>&#x1f50a;</span>
        {SOUND_LABELS[segment.sound_tag ?? ""] ?? segment.sound_tag}
      </span>
    );
  }
  if (segment.type === "pause") {
    return (
      <span className="inline-flex items-center rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
        ...
      </span>
    );
  }
  return <span>{segment.content}</span>;
}

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isScammer = message.role === "scammer";

  return (
    <div className={`flex ${isScammer ? "justify-end" : "justify-start"}`}>
      <div className="max-w-[80%]">
        <div className={`text-xs font-medium mb-1 ${isScammer ? "text-right text-red-400" : "text-emerald-600"}`}>
          {isScammer ? "Arnaqueur" : "Jeanne"}
        </div>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isScammer
              ? "bg-red-500 text-white rounded-br-sm"
              : "bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-sm"
          }`}
        >
          {message.segments ? (
            <div className="space-y-1">
              {message.segments.map((seg, i) => (
                <SegmentBadge key={i} segment={seg} />
              ))}
            </div>
          ) : (
            message.text
          )}
        </div>
      </div>
    </div>
  );
}
