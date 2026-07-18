'use client';

import React, { useState } from 'react';
import { useTheme } from '@/context/ThemeContext';

import styles from './ThemeSwitcher.module.css';

export default function ThemeSwitcher() {
  const { theme, currentTheme, changeTheme, themes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={styles['theme-switcher-container']}>
      <button
        className={styles['theme-switcher-toggle']}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: theme.gradient,
          color: 'white',
          border: `2px solid ${theme.border}`,
        }}
        title="Change Theme"
      >
        🎨
      </button>

      {isOpen && (
        <>
          <div className={styles['theme-switcher-overlay']} onClick={() => setIsOpen(false)} />
          <div className={styles['theme-switcher-dropdown']}>
            <div className={styles['theme-switcher-header']}>
              <h3>Choose Theme</h3>
              <button className={styles['theme-switcher-close']} onClick={() => setIsOpen(false)}>
                ×
              </button>
            </div>
            <div className={styles['theme-switcher-grid']}>
              {Object.entries(themes).map(([key, themeData]) => (
                <button
                  key={key}
                  className={`${styles['theme-option']} ${currentTheme === key ? styles.active : ''}`}
                  onClick={() => {
                    changeTheme(key);
                    setIsOpen(false);
                  }}
                  style={{
                    background: currentTheme === key ? themeData.gradient : 'white',
                    border: `2px solid ${themeData.border}`,
                    color: currentTheme === key ? 'white' : themeData.primary,
                  }}
                >
                  <div
                    className={styles['theme-color-preview']}
                    style={{ background: themeData.gradient }}
                  />
                  <span>{themeData.name}</span>
                  {currentTheme === key && <span className={styles['check-mark']}>✓</span>}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
