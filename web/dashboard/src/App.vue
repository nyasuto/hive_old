<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// Vue 3のComposition APIを使用
// 必要に応じてグローバルな設定やプロバイダーを追加
</script>

<style>
/* グローバルスタイル */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f1f5f9;
  color: #1e293b;
}

#app {
  height: 100vh;
  overflow: hidden;
}

/* スクロールバーのスタイリング */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* ユーティリティクラス */
.text-center {
  text-align: center;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.flex {
  display: flex;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.gap-4 {
  gap: 1rem;
}

.gap-2 {
  gap: 0.5rem;
}

.p-4 {
  padding: 1rem;
}

.p-2 {
  padding: 0.5rem;
}

.m-4 {
  margin: 1rem;
}

.m-2 {
  margin: 0.5rem;
}

/* レスポンシブ用のブレークポイント */
@media (max-width: 640px) {
  .mobile-hidden {
    display: none;
  }
}

@media (max-width: 768px) {
  .tablet-hidden {
    display: none;
  }
}

@media (max-width: 1024px) {
  .desktop-hidden {
    display: none;
  }
}

/* アニメーション */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(-100%);
}

.slide-leave-to {
  transform: translateX(100%);
}

/* フォーカス時のアウトライン */
button:focus-visible,
input:focus-visible,
select:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* 選択不可能なテキスト */
.select-none {
  user-select: none;
}

/* 省略記号 */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 影 */
.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.shadow {
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}
</style>