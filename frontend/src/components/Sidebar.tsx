import React, { useState } from 'react';
import { Activity, LineChart, Settings, LayoutDashboard, Terminal } from 'lucide-react';


interface SidebarProps {
  activeItemId: string;
  onMenuItemClick: (itemId: string) => void; 
}

export default function Sidebar({ 
  activeItemId,
  onMenuItemClick
}: SidebarProps) {

  const menuItems = [
    { icon: <LayoutDashboard size={22} strokeWidth={2} />, label: 'Dashboard', itemId: 'dashboard'},
    { icon: <Activity size={22} strokeWidth={2} />, label: 'Activities', itemId: 'activities'},
    { icon: <LineChart size={22} strokeWidth={2} />, label: 'Analytics', itemId: 'analytics'},
    { icon: <Terminal size={22} strokeWidth={2} />, label: 'Coach Beef 🥩', itemId: 'coach'},
    { icon: <Settings size={22} strokeWidth={2} />, label: 'Settings', style: { marginTop: 'auto' }, itemId: 'settings' },
  ];

  const handleBackgroundClick = (itemId: string) => {
    if (activeItemId === itemId) {
      return
    }
    else {
      activeItemId = itemId;
    }
  };

  return (
    <>
      <div className="sidebar-spacer"></div>

      <nav className="sidebar">
        {menuItems.map((item, index) => {
          // 2. Check if this specific item is the active one
          const isActive = activeItemId === item.itemId;
          
          return (
            <div 
              key={index} 
              // 3. Apply an 'active' class if selected
              className={`menu-item ${isActive ? 'active' : ''}`} 
              style={item.style}
              // 4. Call the parent's function when clicked
              onClick={() => onMenuItemClick(item.itemId)}
            >
              <span className="icon">{item.icon}</span>
              <span className="label">{item.label}</span>
            </div>
          );
        })}
      </nav>
    </>
  );
}