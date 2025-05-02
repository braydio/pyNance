
import '@/styles/tailstyles.css'
import '@/styles/global-colors.css'
import '@/styles/typography.css'
import '@/styles/layout.css'
import '@/styles/buttons.css'
import '@/styles/utilities.css'

import { createApp } from 'vue'
import App from './App.vue'

import router from './router'

const app = createApp(App)

app.use(router)

app.mount('#app')
