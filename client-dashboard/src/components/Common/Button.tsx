import React from 'react';

export const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ className, ...props }) => {
  return <button className={className} {...props} />;
};
