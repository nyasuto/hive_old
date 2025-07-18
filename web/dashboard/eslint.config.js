import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import typescript from '@typescript-eslint/eslint-plugin'
import typescriptParser from '@typescript-eslint/parser'
import vueParser from 'vue-eslint-parser'

export default [
  // Base ESLint recommended rules
  js.configs.recommended,
  
  // Vue 3 recommended rules
  ...vue.configs['flat/recommended'],
  
  // TypeScript and Vue files configuration
  {
    files: ['**/*.{js,mjs,cjs,ts,vue}'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: typescriptParser,
        ecmaVersion: 2022,
        sourceType: 'module',
      },
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        navigator: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        WebSocket: 'readonly',
        HTMLElement: 'readonly',
        SVGElement: 'readonly',
        IntersectionObserver: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        // Node globals
        process: 'readonly',
        Buffer: 'readonly',
        global: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': typescript,
      vue,
    },
    rules: {
      // Vue specific
      'vue/multi-word-component-names': 'off',
      'vue/no-unused-vars': 'error',
      
      // TypeScript
      '@typescript-eslint/no-unused-vars': ['error', { 
        'argsIgnorePattern': '^_',
        'varsIgnorePattern': '^_',
        'ignoreRestSiblings': true
      }],
      
      // General
      'no-unused-vars': ['error', { 
        'argsIgnorePattern': '^_',
        'varsIgnorePattern': '^_',
        'ignoreRestSiblings': true
      }],
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    },
  },
  
  // Ignore patterns
  {
    ignores: [
      'dist/**/*',
      'node_modules/**/*',
      '**/*.d.ts',
      'static/**/*.js',
    ],
  },
]