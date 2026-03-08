import React from 'react';

interface ModalProps {
  open: boolean;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ open, children }) => {
  if (!open) {
    return null;
  }

  return <div className="card">{children}</div>;
};
