import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { 
  HomeIcon, 
  WalletIcon, 
  CubeTransparentIcon, 
  CpuChipIcon, 
  GlobeAltIcon, 
  Cog6ToothIcon,
  MoonIcon,
  SunIcon,
  ArrowLeftIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import './Layout.css';

const Layout = () => {
  const [darkMode, setDarkMode] = useState(localStorage.getItem('darkMode') === 'true');
  const location = useLocation();

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode);
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Set initial dark mode
  React.useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Navigation items
  const navItems = [
    { name: 'Dashboard', path: '/app', icon: HomeIcon },
    { name: 'Wallet', path: '/app/wallet', icon: WalletIcon },
    { name: 'Explorer', path: '/app/explorer', icon: CubeTransparentIcon },
    { name: 'Contracts', path: '/app/contracts', icon: DocumentTextIcon },
    { name: 'Mining', path: '/app/mining', icon: CpuChipIcon },
    { name: 'Network', path: '/app/network', icon: GlobeAltIcon },
    { name: 'Settings', path: '/app/settings', icon: Cog6ToothIcon },
  ];

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="logo-section">
          <Link to="/app" className="logo-link">
            <img 
              src="/assets/logo.png" 
              alt="GlobalCoyn" 
              className="logo" 
            />
            <span className="logo-text">GlobalCoyn</span>
          </Link>
        </div>
        
        {/* Back to Website */}
        <Link to="/" className="back-link">
          <ArrowLeftIcon className="back-icon" />
          <span>Back to Homepage</span>
        </Link>
        
        {/* Navigation */}
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`nav-item ${isActive ? 'active' : ''}`}
              >
                <Icon className="nav-icon" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
        
        {/* Spacer */}
        <div className="sidebar-spacer"></div>
        
        {/* Dark Mode Toggle */}
        <div className="theme-section">
          <button
            onClick={toggleDarkMode}
            className="theme-toggle"
          >
            {darkMode ? (
              <>
                <SunIcon className="theme-icon" />
                <span>Light Mode</span>
              </>
            ) : (
              <>
                <MoonIcon className="theme-icon" />
                <span>Dark Mode</span>
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Main content */}
      <div className="main-content">
        <main className="content-area">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;