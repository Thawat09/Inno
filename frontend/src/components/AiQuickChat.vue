<template>
    <div v-if="visible" class="ai-chat-widget">
        <div class="ai-chat-header">
            <div class="ai-chat-title-wrap">
                <div class="ai-chat-title">AI Assistant</div>
                <div class="ai-chat-subtitle">System support chat</div>
            </div>

            <div class="ai-chat-actions">
                <Button icon="pi pi-minus" text rounded class="topbar-icon-btn small-btn" @click="minimizeChat" />
                <Button icon="pi pi-times" text rounded class="topbar-icon-btn small-btn" @click="closeChat" />
            </div>
        </div>

        <div v-if="!minimized" class="ai-chat-body">
            <div class="ai-chat-messages">
                <div
                    v-for="message in messages"
                    :key="message.id"
                    :class="['ai-chat-message', message.role]"
                >
                    {{ message.text }}
                </div>
            </div>

            <div class="ai-chat-input-wrap">
                <InputText
                    v-model="draftMessage"
                    placeholder="Ask about tickets, standby, SLA..."
                    @keyup.enter="sendMessage"
                />
                <Button icon="pi pi-send" @click="sendMessage" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
    visible: Boolean
})

const emit = defineEmits(['update:visible'])

const CHAT_STORAGE_KEY = 'ai-quick-chat-messages'
const draftMessage = ref('')
const minimized = ref(false)

const messages = ref([
    { id: 1, role: 'assistant', text: 'Hello, how can I help you with the system today?' }
])

onMounted(() => {
    const saved = sessionStorage.getItem(CHAT_STORAGE_KEY)
    if (saved) {
        messages.value = JSON.parse(saved)
    }
})

watch(
    messages,
    (value) => {
        sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(value))
    },
    { deep: true }
)

const sendMessage = () => {
    const text = draftMessage.value.trim()
    if (!text) return

    messages.value.push({
        id: Date.now(),
        role: 'user',
        text
    })

    const lower = text.toLowerCase()

    let reply = 'I understand. This is a mock AI widget for now.'

    if (lower.includes('ticket')) {
        reply = 'You can check ticket details from the Tickets menu or use Global Search.'
    } else if (lower.includes('sla')) {
        reply = 'SLA reports are available from the Reports / SLA page.'
    } else if (lower.includes('standby')) {
        reply = 'Standby data can be viewed from Standby Calendar and Calendar Management.'
    } else if (lower.includes('locked')) {
        reply = 'Locked users can be reviewed from the Locked Users page.'
    }

    messages.value.push({
        id: Date.now() + 1,
        role: 'assistant',
        text: reply
    })

    draftMessage.value = ''
}

const closeChat = () => {
    emit('update:visible', false)
}

const minimizeChat = () => {
    minimized.value = !minimized.value
}
</script>