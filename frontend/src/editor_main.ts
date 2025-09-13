import { createApp } from 'vue'
import { i18n, initializeLanguage } from './i18n'
import Editor from './components/Editor.vue'

const app = createApp(Editor)
app.use(i18n)
app.mount('#app')

// Initialize language after mount
initializeLanguage()
