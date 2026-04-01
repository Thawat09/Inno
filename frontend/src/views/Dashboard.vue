<template>
    <section class="page-section">
        <!-- <div class="dashboard-user-bar">
            <div>
                <div class="dashboard-user-title">Welcome back</div>
                <div class="dashboard-user-info">
                    {{ displayName }} ({{ currentUser?.email || '-' }})
                </div>
            </div>

            <div class="dashboard-user-actions">
                <Button
                    label="My Profile"
                    icon="pi pi-user"
                    severity="secondary"
                    outlined
                    @click="goToProfile"
                />
                <Button
                    label="Tickets"
                    icon="pi pi-ticket"
                    @click="goToTickets"
                />
            </div>
        </div> -->

        <div class="stats-grid">
            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">New Tickets Today</div>
                            <div class="stat-value">{{ dashboardStats.newTicketsToday }}</div>
                            <div class="stat-sub">Incoming tickets received today</div>
                        </div>
                        <div class="stat-icon soft-blue">
                            <i class="pi pi-inbox"></i>
                        </div>
                    </div>
                </template>
            </Card>

            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">Pending Acceptance</div>
                            <div class="stat-value">{{ dashboardStats.pendingAcceptance }}</div>
                            <div class="stat-sub">Waiting for standby confirmation</div>
                        </div>
                        <div class="stat-icon soft-orange">
                            <i class="pi pi-clock"></i>
                        </div>
                    </div>
                </template>
            </Card>

            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">Accepted</div>
                            <div class="stat-value">{{ dashboardStats.acceptedTickets }}</div>
                            <div class="stat-sub">Tickets already accepted</div>
                        </div>
                        <div class="stat-icon soft-cyan">
                            <i class="pi pi-check-circle"></i>
                        </div>
                    </div>
                </template>
            </Card>

            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">Escalated</div>
                            <div class="stat-value">{{ dashboardStats.escalatedTickets }}</div>
                            <div class="stat-sub">Tickets escalated to higher tier</div>
                        </div>
                        <div class="stat-icon soft-purple">
                            <i class="pi pi-arrow-up-right"></i>
                        </div>
                    </div>
                </template>
            </Card>
        </div>

        <div class="stats-grid dashboard-secondary-stats">
            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">No Acceptance</div>
                            <div class="stat-value">{{ dashboardStats.noAcceptanceTickets }}</div>
                            <div class="stat-sub">No one has accepted yet</div>
                        </div>
                        <div class="stat-icon soft-orange">
                            <i class="pi pi-exclamation-triangle"></i>
                        </div>
                    </div>
                </template>
            </Card>

            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">Leave Today</div>
                            <div class="stat-value">{{ dashboardStats.leaveToday }}</div>
                            <div class="stat-sub">Members on leave today</div>
                        </div>
                        <div class="stat-icon soft-blue">
                            <i class="pi pi-calendar-times"></i>
                        </div>
                    </div>
                </template>
            </Card>

            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">Standby Now</div>
                            <div class="stat-value">{{ dashboardStats.standbyNow }}</div>
                            <div class="stat-sub">Active standby members now</div>
                        </div>
                        <div class="stat-icon soft-cyan">
                            <i class="pi pi-users"></i>
                        </div>
                    </div>
                </template>
            </Card>

            <Card class="stat-card">
                <template #content>
                    <div class="stat-top">
                        <div>
                            <div class="stat-title">Near Timeout</div>
                            <div class="stat-value">{{ dashboardStats.nearTimeoutTickets }}</div>
                            <div class="stat-sub">Needs attention soon</div>
                        </div>
                        <div class="stat-icon soft-purple">
                            <i class="pi pi-bell"></i>
                        </div>
                    </div>
                </template>
            </Card>
        </div>

        <div class="dashboard-grid">
            <Card class="content-card">
                <template #title>
                    <div class="section-title-row">
                        <span>Pending / Active Tickets</span>
                        <Button
                            label="View All"
                            text
                            @click="goToTickets"
                        />
                    </div>
                </template>

                <template #content>
                    <DataTable :value="ticketTable" responsiveLayout="scroll" stripedRows>
                        <Column field="ticket_no" header="Ticket No" style="min-width: 140px" />
                        <Column field="subject" header="Subject" style="min-width: 240px" />
                        <Column field="team_name" header="Team" style="min-width: 160px" />
                        <Column field="current_tier" header="Tier" style="min-width: 100px" />
                        <Column field="elapsed" header="Elapsed" style="min-width: 120px" />
                        <Column header="Status" style="min-width: 140px">
                            <template #body="{ data }">
                                <span class="status-badge" :class="ticketStatusClass(data.status)">
                                    {{ data.status }}
                                </span>
                            </template>
                        </Column>
                        <Column header="Action" style="min-width: 120px">
                            <template #body="{ data }">
                                <Button
                                    label="Open"
                                    size="small"
                                    icon="pi pi-arrow-right"
                                    @click="openTicket(data)"
                                />
                            </template>
                        </Column>
                    </DataTable>
                </template>
            </Card>

            <Card class="content-card">
                <template #title>
                    <div class="section-title-row">
                        <span>SLA Overview</span>
                    </div>
                </template>

                <template #content>
                    <Chart type="bar" :data="chartData" :options="chartOptions" />
                </template>
            </Card>
        </div>

        <div class="dashboard-grid">
            <Card class="content-card">
                <template #title>
                    <div class="section-title-row">
                        <span>Current Standby Coverage</span>
                        <Button
                            label="Calendar"
                            text
                            @click="goToCalendar"
                        />
                    </div>
                </template>

                <template #content>
                    <div class="coverage-list">
                        <div
                            v-for="item in standbyCoverage"
                            :key="item.id"
                            class="coverage-card"
                        >
                            <div class="coverage-top">
                                <div class="coverage-team">{{ item.team_name }}</div>
                                <span
                                    class="status-badge"
                                    :class="item.coverage_ok ? 'status-active' : 'status-inactive'"
                                >
                                    {{ item.coverage_ok ? 'Covered' : 'Gap' }}
                                </span>
                            </div>

                            <div class="coverage-shift">{{ item.shift_label }}</div>
                            <div class="coverage-tier-row"><strong>Tier 1:</strong> {{ item.tier1_name || '-' }}</div>
                            <div class="coverage-tier-row"><strong>Tier 2:</strong> {{ item.tier2_name || '-' }}</div>
                            <div class="coverage-tier-row"><strong>Tier 3:</strong> {{ item.tier3_name || '-' }}</div>
                        </div>
                    </div>
                </template>
            </Card>

            <Card class="content-card">
                <template #title>
                    <div class="section-title-row">
                        <span>Important Notifications</span>
                        <Button
                            label="Notifications"
                            text
                            @click="goToNotifications"
                        />
                    </div>
                </template>

                <template #content>
                    <div class="notification-list-dashboard">
                        <div
                            v-for="item in importantNotifications"
                            :key="item.id"
                            class="notification-dashboard-item"
                        >
                            <div class="notification-dashboard-top">
                                <div class="notification-dashboard-title">{{ item.title }}</div>
                                <div class="notification-dashboard-time">{{ item.time }}</div>
                            </div>
                            <div class="notification-dashboard-desc">{{ item.message }}</div>
                        </div>
                    </div>
                </template>
            </Card>
        </div>
    </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser } from '../services/authService'

const router = useRouter()
const currentUser = getCurrentUser()

const displayName = computed(() => {
    const first = currentUser?.first_name?.trim?.() || ''
    const last = currentUser?.last_name?.trim?.() || ''
    const fullName = [first, last].filter(Boolean).join(' ').trim()
    return fullName || currentUser?.name || 'Guest'
})

const dashboardStats = {
    newTicketsToday: 18,
    pendingAcceptance: 6,
    acceptedTickets: 11,
    escalatedTickets: 3,
    noAcceptanceTickets: 2,
    leaveToday: 4,
    standbyNow: 7,
    nearTimeoutTickets: 5
}

const ticketTable = [
    {
        id: 1,
        ticket_no: 'INC000123',
        subject: 'Cannot access AWS console',
        team_name: 'Cloud Operations',
        current_tier: 'Tier 1',
        elapsed: '04m',
        status: 'Pending'
    },
    {
        id: 2,
        ticket_no: 'INC000124',
        subject: 'Production alert on API gateway',
        team_name: 'Security Operations',
        current_tier: 'Tier 2',
        elapsed: '12m',
        status: 'Escalated'
    },
    {
        id: 3,
        ticket_no: 'RITM000245',
        subject: 'Request standby escalation review',
        team_name: 'Standby Support',
        current_tier: 'Tier 1',
        elapsed: '02m',
        status: 'Accepted'
    },
    {
        id: 4,
        ticket_no: 'TASK000981',
        subject: 'Investigate suspicious login attempt',
        team_name: 'Security Operations',
        current_tier: 'Tier 3',
        elapsed: '18m',
        status: 'No Acceptance'
    }
]

const standbyCoverage = [
    {
        id: 1,
        team_name: 'Cloud Operations',
        shift_label: '08:00 - 16:00',
        tier1_name: 'Admin User',
        tier2_name: 'Narin Sukjai',
        tier3_name: 'Mali Kanit',
        coverage_ok: true
    },
    {
        id: 2,
        team_name: 'Security Operations',
        shift_label: '08:00 - 16:00',
        tier1_name: 'Super Admin',
        tier2_name: 'Ploy Jinda',
        tier3_name: '-',
        coverage_ok: true
    },
    {
        id: 3,
        team_name: 'Standby Support',
        shift_label: '16:00 - 00:00',
        tier1_name: 'User One',
        tier2_name: 'Krit Meechai',
        tier3_name: '-',
        coverage_ok: false
    }
]

const importantNotifications = [
    {
        id: 1,
        title: 'Account Locked',
        message: 'A user account was locked after 3 failed login attempts.',
        time: '5 mins ago'
    },
    {
        id: 2,
        title: 'SLA Warning',
        message: 'Ticket INC000124 is nearing response timeout.',
        time: '8 mins ago'
    },
    {
        id: 3,
        title: 'Leave Approved',
        message: 'Admin User leave request has been approved for today.',
        time: '20 mins ago'
    },
    {
        id: 4,
        title: 'Mapping Issue',
        message: 'LINE user mapping could not be resolved automatically.',
        time: '35 mins ago'
    }
]

const chartData = {
    labels: ['Cloud Ops', 'Security Ops', 'Standby Support'],
    datasets: [
        {
            label: 'Avg Response (min)',
            backgroundColor: '#16a34a',
            data: [6, 11, 8]
        },
        {
            label: 'Escalated',
            backgroundColor: '#86efac',
            data: [1, 3, 2]
        },
        {
            label: 'No Acceptance',
            backgroundColor: '#bbf7d0',
            data: [0, 1, 1]
        }
    ]
}

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: '#475569'
            }
        }
    },
    scales: {
        x: {
            ticks: {
                color: '#64748b'
            },
            grid: {
                display: false
            }
        },
        y: {
            ticks: {
                color: '#64748b'
            },
            grid: {
                color: '#f1f5f9'
            }
        }
    }
}

const ticketStatusClass = (status) => {
    switch (status) {
        case 'Accepted':
            return 'status-active'
        case 'Escalated':
            return 'status-pending'
        case 'No Acceptance':
            return 'status-inactive'
        default:
            return 'status-pending'
    }
}

const goToProfile = () => {
    router.push('/profile')
}

const goToTickets = () => {
    router.push('/tickets')
}

const goToCalendar = () => {
    router.push('/calendar')
}

const goToNotifications = () => {
    router.push('/notifications')
}

const openTicket = (ticket) => {
    router.push({
        path: '/ticket-detail',
        query: { ticketNo: ticket.ticket_no }
    })
}
</script>

<style scoped>
.dashboard-user-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.dashboard-secondary-stats {
    margin-top: 1rem;
}

.section-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
}

.coverage-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.coverage-card {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.coverage-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.4rem;
}

.coverage-team {
    font-weight: 700;
    color: var(--text-color);
}

.coverage-shift {
    color: var(--text-muted);
    margin-bottom: 0.75rem;
}

.coverage-tier-row {
    color: var(--text-color);
    margin-bottom: 0.35rem;
}

.notification-list-dashboard {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.notification-dashboard-item {
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1rem;
    background: var(--card-bg);
}

.notification-dashboard-top {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 0.35rem;
}

.notification-dashboard-title {
    font-weight: 700;
    color: var(--text-color);
}

.notification-dashboard-time {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.notification-dashboard-desc {
    color: var(--text-color);
    line-height: 1.45;
}

.status-pending {
    background: #fef3c7;
    color: #92400e;
}

@media (max-width: 768px) {
    .section-title-row {
        align-items: flex-start;
        flex-direction: column;
    }
}
</style>