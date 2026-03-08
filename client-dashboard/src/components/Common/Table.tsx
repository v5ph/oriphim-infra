import React from 'react';

interface TableProps {
  children: React.ReactNode;
}

export const Table: React.FC<TableProps> = ({ children }) => {
  return <table className="min-w-full text-sm">{children}</table>;
};
