import React from "react";

export function SettingsPopup({ onLogout }: { onLogout: () => void }) {
  // Render popup as fixed so it isn't clipped by header/nav overflow
  return (
    <div className="fixed right-4 top-14 w-44 bg-card border border-primary/10 rounded shadow-xl z-[9999]">
      <button
        className="w-full text-left px-4 py-3 text-base font-semibold hover:bg-destructive/10 hover:text-destructive focus:bg-destructive/10 focus:text-destructive transition-colors outline-none"
        onClick={onLogout}
        tabIndex={0}
      >
        Logout
      </button>
    </div>
  );
}
