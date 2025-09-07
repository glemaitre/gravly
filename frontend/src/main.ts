import { createApp } from 'vue'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import App from './App.vue'
import Home from './components/Home.vue'
import RideViewer from './components/RideViewer.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', component: Home },
  { path: '/ride/:id', component: RideViewer, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
