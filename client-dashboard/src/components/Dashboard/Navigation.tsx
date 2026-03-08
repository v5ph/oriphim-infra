import React from 'react';

const items = ['Status', 'Validations', 'Incidents', 'Audit', 'Setup', 'Integrations'];

export const Navigation: React.FC = () => {
  return (
    <nav className="border-b border-subtle bg-white">
      <ul className="flex gap-4 px-8 py-4">
        {items.map((item) => (
          <li key={item} className="text-charcoal-brown font-medium">
            {item}
          </li>
        ))}
      </ul>
    </nav>
  );
};
