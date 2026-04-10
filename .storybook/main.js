/** @type { import('@storybook/react-vite').StorybookConfig } */
const config = {
  stories: [
    'components/**/*.stories.@(js|jsx|ts|tsx|mdx)',
  ],

  addons: [
    '@storybook/addon-essentials',   // Controls, Actions, Docs, Viewport, Backgrounds
    '@storybook/addon-a11y',         // Accessibility checks panel
    '@storybook/addon-designs',      // Figma embed panel
    '@storybook/addon-interactions', // Play functions / interaction testing
  ],

  framework: {
    name: '@storybook/react-vite',
    options: {},
  },

  docs: {
    autodocs: 'tag',
  },
};

export default config;
