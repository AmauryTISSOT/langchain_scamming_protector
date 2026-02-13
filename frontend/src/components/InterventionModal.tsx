import { useState } from "react";

interface Props {
  message: string;
  choices: string[];
  onChoice: (choiceIndex: string) => void;
}

export default function InterventionModal({ message, choices, onChoice }: Props) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const handleConfirm = () => {
    if (selectedIndex !== null) {
      // Choix encodés en "1", "2", "3", "4"
      onChoice(String(selectedIndex + 1));
    }
  };

  const choiceColors = [
    "bg-red-50 border-red-300 hover:bg-red-100 text-red-900",           // Raccroche
    "bg-orange-50 border-orange-300 hover:bg-orange-100 text-orange-900", // Carte
    "bg-purple-50 border-purple-300 hover:bg-purple-100 text-purple-900", // Arrêt cardiaque
    "bg-emerald-50 border-emerald-300 hover:bg-emerald-100 text-emerald-900", // Continuer
  ];

  const selectedColors = [
    "bg-red-100 border-red-500 ring-2 ring-red-500",
    "bg-orange-100 border-orange-500 ring-2 ring-orange-500",
    "bg-purple-100 border-purple-500 ring-2 ring-purple-500",
    "bg-emerald-100 border-emerald-500 ring-2 ring-emerald-500",
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <h2 className="mb-2 text-xl font-bold text-gray-900">
          Intervention requise
        </h2>
        <p className="mb-6 text-sm text-gray-600">{message}</p>

        <div className="mb-6 space-y-3">
          {choices.map((choice, index) => (
            <button
              key={index}
              onClick={() => setSelectedIndex(index)}
              className={`w-full rounded-xl border-2 px-4 py-3 text-left text-sm font-medium transition-all ${
                selectedIndex === index
                  ? selectedColors[index]
                  : choiceColors[index]
              }`}
            >
              {choice}
            </button>
          ))}
        </div>

        <button
          onClick={handleConfirm}
          disabled={selectedIndex === null}
          className="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Confirmer
        </button>
      </div>
    </div>
  );
}
