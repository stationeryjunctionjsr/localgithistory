'use client';

import React, { useState } from 'react';
import { useFont, fonts, fontWeights } from '@/context/FontContext';
import { useTheme } from '@/context/ThemeContext';
import styles from './FontSwitcher.module.css';

export default function FontSwitcher() {
  const { config, updateConfig } = useFont();
  const { theme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={styles['font-switcher-container']}>
      <button
        className={styles['font-switcher-toggle']}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: theme.primary,
          color: 'white',
          border: `2px solid ${theme.border}`,
        }}
        title="Change Typography"
      >
        Aa
      </button>

      {isOpen && (
        <>
          <div className={styles['font-switcher-overlay']} onClick={() => setIsOpen(false)} />
          <div className={styles['font-switcher-dropdown']}>
            <div className={styles['font-switcher-header']}>
              <h3>Typography Settings</h3>
              <button className={styles['font-switcher-close']} onClick={() => setIsOpen(false)}>
                ×
              </button>
            </div>

            <div className={styles['font-switcher-content']}>
              <div className={styles['settings-section']}>
                <label>Font Family</label>
                <div className={styles['font-grid']}>
                  {fonts.map((f) => (
                    <button
                      key={f.name}
                      className={`${styles['font-option']} ${config.family === f.name ? styles.active : ''}`}
                      onClick={() => updateConfig({ family: f.name })}
                      style={{
                        fontFamily: f.name,
                        borderColor: config.family === f.name ? theme.primary : '#eaeaec',
                        backgroundColor: config.family === f.name ? `${theme.primary}10` : 'white',
                      }}
                    >
                      <span className={styles['font-preview']}>Abc</span>
                      <span className={styles['font-name']}>{f.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className={styles['settings-section']}>
                <label>
                  Body Weight: {fontWeights.find((w) => w.value === config.weight)?.label}
                </label>
                <div className={styles['weight-slider-container']}>
                  <input
                    type="range"
                    min="300"
                    max="900"
                    step="100"
                    value={config.weight}
                    onChange={(e) => updateConfig({ weight: e.target.value })}
                    className={styles['weight-slider']}
                    style={{ '--slider-color': theme.primary } as any}
                  />
                  <div className={styles['weight-labels']}>
                    <span>300</span>
                    <span>900</span>
                  </div>
                </div>
              </div>

              <div className={styles['settings-section']}>
                <label>
                  Heading Weight: {fontWeights.find((w) => w.value === config.headingWeight)?.label}
                </label>
                <div className={styles['weight-slider-container']}>
                  <input
                    type="range"
                    min="300"
                    max="900"
                    step="100"
                    value={config.headingWeight}
                    onChange={(e) => updateConfig({ headingWeight: e.target.value })}
                    className={styles['weight-slider']}
                    style={{ '--slider-color': theme.primary } as any}
                  />
                  <div className={styles['weight-labels']}>
                    <span>300</span>
                    <span>900</span>
                  </div>
                </div>
              </div>

              <div className={styles['preview-box']} style={{ fontFamily: config.family }}>
                <h4 style={{ fontWeight: config.headingWeight }}>The Quick Brown Fox</h4>
                <p style={{ fontWeight: config.weight }}>
                  Jumps over the lazy dog. Previewing your selected typography and weight settings.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
