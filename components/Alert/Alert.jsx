/**
 * BlackBirdDS — Alert
 * -------------------
 * Contextual feedback message with four semantic types.
 * Uses CSS custom properties from the BlackBirdDS token system,
 * falling back to hardcoded values for environments without the
 * token stylesheet loaded.
 *
 * @example
 * <Alert type="success" title="Saved!" description="Changes published." dismissible />
 */

import { useState } from 'react';

// ── Token map (mirrors Figma Semantic Colors collection) ─────────────────────
const TOKENS = {
  success: {
    bg:     'var(--color-success-soft,   #F0FDF4)',
    border: 'var(--color-success-border, #B9F8CF)',
    text:   'var(--color-success-text,   #008236)',
    bar:    'var(--color-success-default, #00A63E)',
  },
  warning: {
    bg:     'var(--color-warning-soft,   #FFFBEB)',
    border: 'var(--color-warning-border, #FEE685)',
    text:   'var(--color-warning-text,   #BB4D00)',
    bar:    'var(--color-warning-default, #E17100)',
  },
  error: {
    bg:     'var(--color-error-soft,   #FEF2F2)',
    border: 'var(--color-error-border, #FFC9C9)',
    text:   'var(--color-error-text,   #C10007)',
    bar:    'var(--color-error-default, #E7000B)',
  },
  info: {
    bg:     'var(--color-info-soft,   #F0F9FF)',
    border: 'var(--color-info-border, #B8E6FE)',
    text:   'var(--color-info-text,   #0069A8)',
    bar:    'var(--color-info-default, #0084D1)',
  },
};

// ── Icons ────────────────────────────────────────────────────────────────────
function AlertIcon({ type }) {
  const style = { width: 18, height: 18, flexShrink: 0, marginTop: 2 };

  if (type === 'success') return (
    <svg viewBox="0 0 20 20" fill="none" style={style} aria-hidden="true">
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M6.5 10l2.5 2.5 4.5-5" stroke="currentColor" strokeWidth="1.6"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );

  if (type === 'warning') return (
    <svg viewBox="0 0 20 20" fill="none" style={style} aria-hidden="true">
      <path d="M10 3.5L17.5 16.5h-15L10 3.5z" stroke="currentColor"
            strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M10 9v4M10 14.5v.5" stroke="currentColor" strokeWidth="1.8"
            strokeLinecap="round" />
    </svg>
  );

  if (type === 'error') return (
    <svg viewBox="0 0 20 20" fill="none" style={style} aria-hidden="true">
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M10 6v5M10 13.5v.5" stroke="currentColor" strokeWidth="1.8"
            strokeLinecap="round" />
    </svg>
  );

  // info (default)
  return (
    <svg viewBox="0 0 20 20" fill="none" style={style} aria-hidden="true">
      <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M10 9v5M10 6.5v.5" stroke="currentColor" strokeWidth="1.8"
            strokeLinecap="round" />
    </svg>
  );
}

// ── Alert ────────────────────────────────────────────────────────────────────
/**
 * @param {'success'|'warning'|'error'|'info'} type
 *   Semantic intent — determines colour and icon.
 * @param {string}   title        Bold heading of the alert.
 * @param {string}   description  Supporting description text.
 * @param {boolean}  dismissible  Show the close (×) button.
 * @param {function} onDismiss    Callback fired when dismissed.
 */
export function Alert({
  type        = 'info',
  title       = '',
  description = '',
  dismissible = false,
  onDismiss,
}) {
  const [visible, setVisible] = useState(true);
  if (!visible) return null;

  const tok = TOKENS[type] ?? TOKENS.info;

  function dismiss() {
    setVisible(false);
    onDismiss?.();
  }

  return (
    <div
      role="alert"
      style={{
        display:        'flex',
        alignItems:     'flex-start',
        gap:            12,
        padding:        '14px 16px',
        background:     tok.bg,
        border:         `1px solid ${tok.border}`,
        borderRadius:   8,
        overflow:       'hidden',
        position:       'relative',
        color:          tok.text,
      }}
    >
      {/* Left accent bar */}
      <div
        aria-hidden="true"
        style={{
          position:     'absolute',
          left: 0, top: 0, bottom: 0,
          width:        4,
          background:   tok.bar,
          borderRadius: '2px 0 0 2px',
        }}
      />

      {/* Icon */}
      <AlertIcon type={type} />

      {/* Body */}
      <div style={{ flex: 1, minWidth: 0, paddingLeft: 2 }}>
        {title && (
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 3 }}>
            {title}
          </div>
        )}
        {description && (
          <div style={{ fontSize: 13, lineHeight: 1.65, opacity: 0.82 }}>
            {description}
          </div>
        )}
      </div>

      {/* Dismiss button */}
      {dismissible && (
        <button
          aria-label="Dismiss alert"
          onClick={dismiss}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: tok.text, opacity: 0.55, flexShrink: 0,
            display: 'flex', alignItems: 'center', padding: 2,
          }}
        >
          <svg viewBox="0 0 16 16" fill="none" width={14} height={14} aria-hidden="true">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor"
                  strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default Alert;
