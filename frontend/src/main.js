import '@/assets/css/main.css'
import '@/assets/css/theme.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import { createPinia } from 'pinia'
import clickOutside from '@/directives/clickOutside'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Toast)
app.directive('click-outside', clickOutside)
app.mount('#app')
