<template>
    <div class="layout-wrapper" :class="{
        'layout-sidebar-open': sidebarOpen,
        'layout-sidebar-collapsed': !sidebarOpen
    }">
        <AppTopbar @toggle-sidebar="toggleSidebar" />

        <AppSidebar :open="sidebarOpen" :isMobile="isMobile" @close-sidebar="closeSidebar" />

        <div v-if="sidebarOpen && isMobile" class="layout-mask" @click="closeSidebar"></div>

        <main class="layout-main">
            <div class="layout-main-inner">
                <router-view />
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import AppTopbar from '../components/AppTopbar.vue'
import AppSidebar from '../components/AppSidebar.vue'

const windowWidth = ref(window.innerWidth)
const sidebarOpen = ref(true)

const isMobile = computed(() => windowWidth.value <= 1024)

const updateWindow = () => {
    windowWidth.value = window.innerWidth

    if (window.innerWidth <= 1024) {
        sidebarOpen.value = false
    } else {
        sidebarOpen.value = true
    }
}

const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
    sidebarOpen.value = false
}

onMounted(() => {
    updateWindow()
    window.addEventListener('resize', updateWindow)
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', updateWindow)
})
</script>