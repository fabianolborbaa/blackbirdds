import { Alert } from './Alert';

// ── Meta ─────────────────────────────────────────────────────────────────────
/** @type { import('@storybook/react').Meta<typeof Alert> } */
export default {
  title:     'BlackBirdDS/Alert',
  component:  Alert,
  tags:      ['autodocs'],

  // Figma embed (shows the Figma frame in the Designs panel)
  parameters: {
    design: {
      type: 'figma',
      url:  'https://www.figma.com/file/2Ov115BSkN5jNisHpc6ZXq?node-id=77-0',
    },
    docs: {
      description: {
        component: `
Contextual feedback messages that communicate status, warnings, errors,
or informational content to the user.

Each alert uses a **left accent bar** and matching **SVG icon** to signal
intent at a glance. The colours are driven by BlackBirdDS semantic tokens,
so they automatically adapt to Light and Dark mode.

\`\`\`bash
import { Alert } from '@/components/Alert';
\`\`\`
        `.trim(),
      },
    },
  },

  // Controls configuration
  argTypes: {
    type: {
      control: 'select',
      options: ['success', 'warning', 'error', 'info'],
      description: 'Semantic intent — determines colour and icon.',
      table: {
        type:         { summary: "'success' | 'warning' | 'error' | 'info'" },
        defaultValue: { summary: "'info'" },
      },
    },
    title: {
      control:     'text',
      description: 'Bold heading of the alert.',
    },
    description: {
      control:     'text',
      description: 'Supporting description text shown below the title.',
    },
    dismissible: {
      control:     'boolean',
      description: 'Show the close (×) button.',
      table: {
        type:         { summary: 'boolean' },
        defaultValue: { summary: 'false' },
      },
    },
    onDismiss: {
      action:      'dismissed',
      description: 'Callback fired when the user clicks the dismiss button.',
    },
  },
};

// ── Stories ──────────────────────────────────────────────────────────────────

export const Success = {
  args: {
    type:        'success',
    title:       'Changes saved successfully',
    description: 'Your design tokens have been published to all connected projects.',
    dismissible: true,
  },
};

export const Warning = {
  args: {
    type:        'warning',
    title:       'Unsaved changes detected',
    description: 'You have uncommitted token changes. Publish before deploying.',
    dismissible: true,
  },
};

export const Error = {
  args: {
    type:        'error',
    title:       'Sync failed',
    description: 'Could not connect to Figma API. Check your token and try again.',
    dismissible: true,
  },
};

export const Info = {
  args: {
    type:        'info',
    title:       'Scheduled sync active',
    description: 'Tokens sync automatically every day at 02:00 UTC.',
    dismissible: false,
  },
};

// ── All four types side by side ───────────────────────────────────────────────
export const AllTypes = {
  name:   'All Types',
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 560 }}>
      <Alert type="success" title="Success"  description="Operation completed successfully." dismissible />
      <Alert type="warning" title="Warning"  description="Something needs your attention." dismissible />
      <Alert type="error"   title="Error"    description="Something went wrong. Please try again." dismissible />
      <Alert type="info"    title="Info"     description="Here's something you should know." />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All four semantic types rendered together for visual comparison.',
      },
    },
  },
};

// ── Title only (no description) ───────────────────────────────────────────────
export const TitleOnly = {
  name: 'Title Only',
  args: {
    type:        'info',
    title:       'Your session will expire in 5 minutes.',
    description: '',
    dismissible: true,
  },
};

// ── Non-dismissible ───────────────────────────────────────────────────────────
export const NonDismissible = {
  name: 'Non-dismissible',
  args: {
    type:        'error',
    title:       'Account suspended',
    description: 'Contact support to restore access to your account.',
    dismissible: false,
  },
};

// ── Playground (fully interactive) ───────────────────────────────────────────
export const Playground = {
  args: {
    type:        'info',
    title:       'Try the controls →',
    description: 'Use the Controls panel below to customize this alert in real time.',
    dismissible: true,
  },
};
