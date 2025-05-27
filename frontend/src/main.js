import '@/assets/css/main.css'

import { createApp } from 'vue'
import App from './App.vue'

import Toastify from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

import router from './router'

const app = createApp(App)

app.use(Toastify, {
  autoClose: 3000,
  position: 'top-right',
})

app.use(router)

app.mount('#app')
