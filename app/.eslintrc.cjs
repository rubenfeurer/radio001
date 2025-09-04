module.exports = {
  root: true,
  env: {
    browser: true,
    node: true
  },
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 2022,
    sourceType: 'module'
  },
  extends: [
    '@nuxtjs/eslint-config-typescript',
    'plugin:vue/vue3-recommended'
  ],
  plugins: [],
  rules: {
    // Vue rules - relaxed for development
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'off',
    'vue/require-default-prop': 'off',
    'vue/require-prop-types': 'off',
    'vue/no-unused-vars': 'warn',
    'vue/attributes-order': 'off',
    'vue/max-attributes-per-line': 'off',
    'vue/first-attribute-linebreak': 'off',
    'vue/html-closing-bracket-newline': 'off',
    'vue/singleline-html-element-content-newline': 'off',
    'vue/html-self-closing': 'off',
    'vue/html-indent': 'off',

    // TypeScript rules
    '@typescript-eslint/no-unused-vars': 'warn',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/ban-ts-comment': 'warn',

    // General rules - relaxed for development
    'no-console': 'off', // Allow console in development
    'no-debugger': 'warn',
    'no-undef': 'off', // TypeScript handles this
    'prefer-const': 'error',
    'no-var': 'error',
    'object-shorthand': 'off',
    'prefer-arrow-callback': 'off',
    'quote-props': 'off',
    'quotes': 'off',
    'semi': 'off',
    'comma-dangle': 'off',
    'indent': 'off',
    'space-before-function-paren': 'off',
    'keyword-spacing': 'off',
    'space-infix-ops': 'off',
    'eol-last': 'off',
    'no-trailing-spaces': 'off',
    'no-multiple-empty-lines': 'off',
    'curly': 'off', // Allow single-line if statements
    'require-await': 'off'
  },
  ignorePatterns: [
    '.nuxt/',
    '.output/',
    'dist/',
    'node_modules/',
    '*.d.ts'
  ]
}
