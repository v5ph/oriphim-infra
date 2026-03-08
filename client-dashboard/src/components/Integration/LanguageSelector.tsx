import React from 'react';

export type ProgrammingLanguage = 'python' | 'typescript' | 'curl';

interface LanguageSelectorProps {
  selected: ProgrammingLanguage;
  onChange: (language: ProgrammingLanguage) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ selected, onChange }) => {
  const languages: Array<{ value: ProgrammingLanguage; label: string }> = [
    { value: 'python', label: 'Python' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'curl', label: 'cURL' },
  ];

  return (
    <div className="card">
      <h3 className="text-lg font-bold text-carbon-black mb-4">Programming Language</h3>
      <div className="flex flex-wrap gap-3">
        {languages.map((lang) => (
          <button
            key={lang.value}
            onClick={() => onChange(lang.value)}
            className={`px-6 py-3 rounded font-medium transition-colors ${
              selected === lang.value
                ? 'bg-blood-red text-floral-white'
                : 'bg-white border border-subtle text-carbon-black hover:bg-floral-white'
            }`}
          >
            {lang.label}
          </button>
        ))}
      </div>
    </div>
  );
};
