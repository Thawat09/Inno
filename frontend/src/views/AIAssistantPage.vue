<template>
    <section class="page-section">
        <Card class="content-card">
            <template #title>
                <div class="page-header">
                    <div>
                        <div class="page-title">AI Assistant</div>
                        <div class="page-subtitle">
                            Chat with AI to assist ticket routing, investigation, and decision making.
                        </div>
                    </div>
                </div>
            </template>

            <template #content>
                <div class="ai-layout">

                    <!-- LEFT: CHAT -->
                    <div class="chat-section">
                        <div class="chat-box">
                            <div
                                v-for="(msg, index) in messages"
                                :key="index"
                                class="chat-message"
                                :class="msg.role"
                            >
                                <div class="chat-bubble">
                                    {{ msg.text }}
                                </div>
                            </div>
                        </div>

                        <div class="chat-input">
                            <InputText
                                v-model="userInput"
                                placeholder="Ask something..."
                                @keyup.enter="sendMessage"
                            />
                            <Button icon="pi pi-send" @click="sendMessage" />
                        </div>
                    </div>

                    <!-- RIGHT: CONTEXT -->
                    <div class="context-section">
                        <Card class="context-card">
                            <template #title>
                                <span>Context</span>
                            </template>

                            <template #content>
                                <div class="context-block">
                                    <div class="context-title">Current Ticket</div>

                                    <div v-if="selectedTicket">
                                        <div><b>{{ selectedTicket.ticket_no }}</b></div>
                                        <div>{{ selectedTicket.subject }}</div>
                                        <div class="sub-text">
                                            {{ selectedTicket.team_name }} |
                                            {{ selectedTicket.current_tier }}
                                        </div>
                                    </div>

                                    <div v-else class="empty-text">
                                        No ticket selected
                                    </div>
                                </div>

                                <div class="context-block">
                                    <div class="context-title">Quick Actions</div>

                                    <div class="quick-actions">
                                        <Button
                                            label="Suggest Team"
                                            size="small"
                                            outlined
                                            @click="quickAsk('Which team should handle this?')"
                                        />
                                        <Button
                                            label="Suggest User"
                                            size="small"
                                            outlined
                                            @click="quickAsk('Who should handle this ticket?')"
                                        />
                                        <Button
                                            label="Escalation Advice"
                                            size="small"
                                            outlined
                                            @click="quickAsk('Should I escalate this?')"
                                        />
                                    </div>
                                </div>
                            </template>
                        </Card>
                    </div>

                </div>

                <div class="mock-note mt-3">
                    This AI assistant is currently using mock responses. Ready for integration with LLM backend.
                </div>
            </template>
        </Card>
    </section>
</template>

<script setup>
import { ref } from "vue";

const userInput = ref("");
const messages = ref([
    {
        role: "assistant",
        text: "Hello! How can I help you today?"
    }
]);

const selectedTicket = ref({
    ticket_no: "INC000123",
    subject: "Cannot access AWS console",
    team_name: "Cloud Operations",
    current_tier: "Tier 1"
});

// MOCK AI RESPONSE
const mockAI = (input) => {
    if (input.toLowerCase().includes("team")) {
        return "Based on the ticket, Cloud Operations is the most suitable team.";
    }

    if (input.toLowerCase().includes("user")) {
        return "Recommended assignee: Admin User (highest availability).";
    }

    if (input.toLowerCase().includes("escalate")) {
        return "Escalation is not required yet. Wait for Tier 1 timeout.";
    }

    return "I suggest reviewing ticket context or assigning to the default team.";
};

const sendMessage = () => {
    if (!userInput.value.trim()) return;

    messages.value.push({
        role: "user",
        text: userInput.value
    });

    const reply = mockAI(userInput.value);

    setTimeout(() => {
        messages.value.push({
            role: "assistant",
            text: reply
        });
    }, 400);

    userInput.value = "";
};

const quickAsk = (text) => {
    userInput.value = text;
    sendMessage();
};
</script>

<style scoped>
.ai-layout {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1rem;
}

/* CHAT */
.chat-section {
    display: flex;
    flex-direction: column;
    height: 500px;
}

.chat-box {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    background: var(--card-bg);
}

.chat-message {
    margin-bottom: 0.6rem;
    display: flex;
}

.chat-message.user {
    justify-content: flex-end;
}

.chat-message.assistant {
    justify-content: flex-start;
}

.chat-bubble {
    padding: 0.6rem 0.9rem;
    border-radius: 12px;
    max-width: 75%;
    font-size: 0.95rem;
}

.chat-message.user .chat-bubble {
    background: #dcfce7;
}

.chat-message.assistant .chat-bubble {
    background: #f1f5f9;
}

.chat-input {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

/* CONTEXT */
.context-card {
    height: 100%;
}

.context-block {
    margin-bottom: 1rem;
}

.context-title {
    font-weight: 700;
    margin-bottom: 0.4rem;
}

.sub-text {
    font-size: 0.85rem;
    color: var(--text-muted);
}

.empty-text {
    color: var(--text-muted);
}

.quick-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.mt-3 {
    margin-top: 1rem;
}

@media (max-width: 1024px) {
    .ai-layout {
        grid-template-columns: 1fr;
    }
}
</style>