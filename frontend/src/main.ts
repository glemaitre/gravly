import { createApp } from 'vue'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { i18n, initializeLanguage } from './i18n'
import App from './App.vue'
import Editor from './components/Editor.vue'
import LandingPage from './components/LandingPage.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', component: LandingPage },
  { path: '/editor', component: Editor }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.use(i18n)
app.mount('#app')

// Initialize language after mount
initializeLanguage()
