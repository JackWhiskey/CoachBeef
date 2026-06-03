import React from 'react';

interface SettingsPanelProps {
  useImperialDistances: boolean;
  setUseImperialDistances: (value: boolean) => void;
}

export default function SettingsPanel({ 
  useImperialDistances, 
  setUseImperialDistances 
}: SettingsPanelProps) {
  return (
    <aside className="chat-panel"> {/* Reusing the right-side panel layout */}
      <h3 style={{ marginBottom: "20px" }}>Settings</h3>
      
      <div className="setting-row">
        <div className="setting-info">
          <h4>Use Imperial Distances</h4>
          <p>Display distances in miles and paces in min/mi instead of kilometers.</p>
        </div>
        
        {/* Modern Toggle Switch */}
        <label className="toggle-switch">
          <input 
            type="checkbox" 
            checked={useImperialDistances}
            onChange={(e) => setUseImperialDistances(e.target.checked)}
          />
          <span className="toggle-slider"></span>
        </label>
      </div>

    </aside>
  );
}