/** @type { import("eslint").Linter.Config } */
module.exports = {
	root: true,
	extends: ['eslint:recommended'],
	env: {
		browser: true,
		es2017: true,
		node: true
	},
	parserOptions: {
		ecmaVersion: 2020,
		sourceType: 'module'
	},
	rules: {
		'no-unused-vars': 'warn',
		'no-console': 'off'
	},
	ignorePatterns: ['node_modules/', '.svelte-kit/', 'build/', 'dist/']
};
