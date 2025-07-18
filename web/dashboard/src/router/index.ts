import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Conversations from '@/views/Conversations.vue'
import Command from '@/views/Command.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/conversations',
      name: 'conversations',
      component: Conversations
    },
    {
      path: '/command',
      name: 'command',
      component: Command
    }
  ]
})

export default router