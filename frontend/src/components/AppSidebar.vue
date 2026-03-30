<template>
    <aside class="layout-sidebar" :class="{ 'layout-sidebar-active': open }">
        <div class="sidebar-inner">

            <!-- HOME -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">HOME</div>

                <router-link to="/" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-home"></i>
                    <span>Dashboard</span>
                </router-link>
            </div>

            <!-- TICKETS -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">TICKETS</div>

                <router-link to="/tickets" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-ticket"></i>
                    <span>Tickets</span>
                </router-link>

                <router-link to="/ticket-detail" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-file"></i>
                    <span>Ticket Detail</span>
                </router-link>

                <router-link to="/acceptance-monitor" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-clock"></i>
                    <span>Acceptance Monitor</span>
                </router-link>

                <router-link to="/manual-override" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-pencil"></i>
                    <span>Manual Override</span>
                </router-link>
            </div>

            <!-- STANDBY -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">STANDBY</div>

                <router-link to="/calendar" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-calendar"></i>
                    <span>Standby Calendar</span>
                </router-link>

                <router-link to="/calendar-management" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-cog"></i>
                    <span>Calendar Management</span>
                </router-link>

                <router-link to="/leave" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-user-minus"></i>
                    <span>Leave / Availability</span>
                </router-link>

                <router-link to="/escalation-rule" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-arrow-up"></i>
                    <span>Escalation Rule</span>
                </router-link>
            </div>

            <!-- USERS -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">USERS</div>

                <router-link to="/teams" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-users"></i>
                    <span>Teams & Members</span>
                </router-link>

                <router-link to="/profile" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-user"></i>
                    <span>My Profile</span>
                </router-link>

                <router-link to="/users" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-id-card"></i>
                    <span>User Management</span>
                </router-link>

                <router-link to="/locked-users" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-lock"></i>
                    <span>Locked Users</span>
                </router-link>
            </div>

            <!-- LINE & ALERT -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">LINE & ALERT</div>

                <router-link to="/notifications" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-bell"></i>
                    <span>Notifications</span>
                </router-link>

                <router-link to="/line-monitor" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-comment"></i>
                    <span>LINE Monitoring</span>
                </router-link>
            </div>

            <!-- REPORTS -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">REPORTS</div>

                <router-link to="/reports" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-chart-bar"></i>
                    <span>Reports / SLA</span>
                </router-link>

                <router-link to="/audit-log" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-history"></i>
                    <span>Audit Log</span>
                </router-link>

                <router-link to="/ai-audit" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-search"></i>
                    <span>AI Audit</span>
                </router-link>
            </div>

            <!-- AI -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">AI</div>

                <router-link to="/ai" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-send"></i>
                    <span>AI Assistant</span>
                </router-link>
            </div>

            <!-- TOOLS -->
            <div class="sidebar-section">
                <div class="sidebar-section-title">TOOLS</div>

                <router-link to="/data-mapping" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-database"></i>
                    <span>Data Mapping</span>
                </router-link>

                <router-link to="/search" class="sidebar-link" @click="handleClick">
                    <i class="pi pi-search"></i>
                    <span>Global Search</span>
                </router-link>
            </div>

        </div>
    </aside>
</template>

<script setup>
const props = defineProps({
    open: Boolean,
    isMobile: Boolean
})

const emit = defineEmits(['close-sidebar'])

const handleClick = () => {
    if (props.isMobile) {
        emit('close-sidebar')
    }
}
</script>