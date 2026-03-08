import React from 'react';

interface ChainVerificationBadgeProps {
  verified: boolean;
  isLoading?: boolean;
  onVerify?: () => void;
}

export const ChainVerificationBadge: React.FC<ChainVerificationBadgeProps> = ({
  verified,
  isLoading = false,
  onVerify,
}) => {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <div
          className={`w-3 h-3 rounded-full ${
            verified ? 'bg-green-500' : 'bg-blood-red'
          }`}
        />
        <span
          className={`font-medium ${
            verified ? 'text-green-700' : 'text-blood-red'
          }`}
        >
          Chain {verified ? 'Verified' : 'Broken'}
        </span>
      </div>

      {onVerify && (
        <button
          onClick={onVerify}
          disabled={isLoading}
          className="btn-secondary px-3 py-1 rounded text-sm disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading && (
            <div className="animate-spin h-3 w-3 border-2 border-charcoal-brown border-t-transparent rounded-full" />
          )}
          {isLoading ? 'Verifying...' : 'Re-verify'}
        </button>
      )}
    </div>
  );
};
