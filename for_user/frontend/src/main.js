import { createApp } from 'vue'
import { Quasar, Notify } from 'quasar'
import router from './router'

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css'

// Import Quasar css
import 'quasar/src/css/index.sass'

import './style.css'

import App from './App.vue'

const app = createApp(App)

app.use(Quasar, {
  plugins: {
      Notify
  }, // import Quasar plugins and add here
})

app.use(router)

app.mount('#app')
