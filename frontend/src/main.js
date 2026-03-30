import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'

import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Chart from 'primevue/chart'
import Avatar from 'primevue/avatar'
import Badge from 'primevue/badge'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import Menu from 'primevue/menu'
import Password from 'primevue/password'
import Message from 'primevue/message'

import 'primeicons/primeicons.css'
import './assets/styles/main.css'

import { initMockData } from './utils/seedUsers'
import { initTheme } from './utils/theme'

initMockData()
initTheme()

const app = createApp(App)

app.use(router)

app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: '.app-dark'
        }
    }
})

app.component('Button', Button)
app.component('Card', Card)
app.component('InputText', InputText)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Chart', Chart)
app.component('Avatar', Avatar)
app.component('Badge', Badge)
app.component('InputNumber', InputNumber)
app.component('Textarea', Textarea)
app.component('Dropdown', Dropdown)
app.component('Menu', Menu)
app.component('Password', Password)
app.component('Message', Message)

app.mount('#app')