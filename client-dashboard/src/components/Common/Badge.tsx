import React from 'react';

interface BadgeProps {
  className?: string;
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ className, children }) => {
  return <span className={className}>{children}</span>;
};
