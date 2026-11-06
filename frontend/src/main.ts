import { createApp } from 'vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import App from './App.vue'
import router from './router'
import { loadSession } from './data'
import './index.css'

dayjs.extend(relativeTime)

loadSession().finally(() => createApp(App).use(router).mount('#app'))
