<template>
    <div>
        <!-- <div class="dashboard-user-bar">
            <div>
                <div class="dashboard-user-title">Welcome back</div>
                <div class="dashboard-user-info">
                    {{ currentUser?.name || 'Guest' }} ({{ currentUser?.email || '-' }})
                </div>
            </div>

            <Button
                label="Logout"
                icon="pi pi-sign-out"
                severity="danger"
                outlined
                @click="handleLogout"
            />
        </div> -->

        <section class="page-section">
            <div class="stats-grid">
                <Card class="stat-card">
                    <template #content>
                        <div class="stat-top">
                            <div>
                                <div class="stat-title">Orders</div>
                                <div class="stat-value">152</div>
                                <div class="stat-sub success-text">24 new since last visit</div>
                            </div>
                            <div class="stat-icon soft-blue">
                                <i class="pi pi-shopping-cart"></i>
                            </div>
                        </div>
                    </template>
                </Card>

                <Card class="stat-card">
                    <template #content>
                        <div class="stat-top">
                            <div>
                                <div class="stat-title">Revenue</div>
                                <div class="stat-value">$2.100</div>
                                <div class="stat-sub success-text">%52+ since last week</div>
                            </div>
                            <div class="stat-icon soft-orange">
                                <i class="pi pi-dollar"></i>
                            </div>
                        </div>
                    </template>
                </Card>

                <Card class="stat-card">
                    <template #content>
                        <div class="stat-top">
                            <div>
                                <div class="stat-title">Customers</div>
                                <div class="stat-value">28441</div>
                                <div class="stat-sub success-text">520 newly registered</div>
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
                                <div class="stat-title">Comments</div>
                                <div class="stat-value">152 Unread</div>
                                <div class="stat-sub success-text">85 responded</div>
                            </div>
                            <div class="stat-icon soft-purple">
                                <i class="pi pi-comment"></i>
                            </div>
                        </div>
                    </template>
                </Card>
            </div>

            <div class="dashboard-grid">
                <Card class="content-card">
                    <template #title>Recent Sales</template>
                    <template #content>
                        <DataTable :value="products" responsiveLayout="scroll" class="sales-table">
                            <Column field="image" header="Image">
                                <template #body="{ data }">
                                    <img :src="data.image" :alt="data.name" class="product-image" />
                                </template>
                            </Column>

                            <Column field="name" header="Name"></Column>
                            <Column field="price" header="Price"></Column>

                            <Column header="View">
                                <template #body>
                                    <Button icon="pi pi-search" text rounded class="text-green" />
                                </template>
                            </Column>
                        </DataTable>
                    </template>
                </Card>

                <Card class="content-card">
                    <template #title>Revenue Stream</template>
                    <template #content>
                        <Chart type="bar" :data="chartData" :options="chartOptions" />
                    </template>
                </Card>
            </div>
        </section>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { getCurrentUser, logout } from '../services/authService'

const router = useRouter()
const currentUser = getCurrentUser()

const handleLogout = () => {
    logout()
    router.push('/login')
}

const products = [
    {
        name: 'Bamboo Watch',
        price: '$65.00',
        image: 'https://primefaces.org/cdn/primevue/images/product/bamboo-watch.jpg'
    },
    {
        name: 'Black Watch',
        price: '$72.00',
        image: 'https://primefaces.org/cdn/primevue/images/product/black-watch.jpg'
    },
    {
        name: 'Blue Band',
        price: '$79.00',
        image: 'https://primefaces.org/cdn/primevue/images/product/blue-band.jpg'
    },
    {
        name: 'Blue T-Shirt',
        price: '$29.00',
        image: 'https://primefaces.org/cdn/primevue/images/product/blue-t-shirt.jpg'
    },
    {
        name: 'Bracelet',
        price: '$15.00',
        image: 'https://primefaces.org/cdn/primevue/images/product/bracelet.jpg'
    }
]

const chartData = {
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
    datasets: [
        {
            label: 'Subscriptions',
            backgroundColor: '#16a34a',
            data: [4000, 10000, 15000, 4000]
        },
        {
            label: 'Advertising',
            backgroundColor: '#4ade80',
            data: [2000, 8000, 2500, 7200]
        },
        {
            label: 'Affiliate',
            backgroundColor: '#a7f3d0',
            data: [4000, 5000, 3000, 7500]
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
</script>