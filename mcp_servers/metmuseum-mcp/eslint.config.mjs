import antfu from '@antfu/eslint-config';

export default antfu({
  formatters: true,
  stylistic: {
    semi: true,
    indent: 2,
    quotes: 'single',
  },
});
