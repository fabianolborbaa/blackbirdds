import '../components/tokens.css';

/** @type { import('@storybook/react').Preview } */
const preview = {
  parameters: {
    // ── Backgrounds ───────────────────────────────────────────────────────────
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#FFFFFF' },
        { name: 'surface', value: '#F9FAFB' },
        { name: 'dark', value: '#101828' },
      ],
    },

    // ── Viewport presets ──────────────────────────────────────────────────────
    viewport: {
      viewports: {
        mobile:  { name: 'Mobile',  styles: { width: '390px',  height: '844px' } },
        tablet:  { name: 'Tablet',  styles: { width: '768px',  height: '1024px' } },
        desktop: { name: 'Desktop', styles: { width: '1440px', height: '900px' } },
      },
    },

    // ── Docs page defaults ────────────────────────────────────────────────────
    docs: {
      toc: true,
    },

    // ── Controls defaults ─────────────────────────────────────────────────────
    controls: {
      matchers: {
        color: /(bg|color|fill|stroke|border|background)$/i,
        date:  /date$/i,
      },
    },
  },
};

export default preview;
