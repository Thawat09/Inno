<template>
    <section class="page-section">
        <div class="single-grid">
            <Card class="content-card">
                <template #title>Table Demo</template>
                <template #content>
                    <DataTable :value="users" paginator :rows="5" responsiveLayout="scroll">
                        <Column field="name" header="Name"></Column>
                        <Column field="email" header="Email"></Column>
                        <Column field="department" header="Department"></Column>
                        <Column field="status" header="Status">
                            <template #body="{ data }">
                                <span class="status-badge"
                                    :class="data.status === 'Active' ? 'status-active' : 'status-inactive'">
                                    {{ data.status }}
                                </span>
                            </template>
                        </Column>
                    </DataTable>
                </template>
            </Card>
        </div>
    </section>
</template>

<script setup>
const users = [
    { name: 'John Doe', email: 'john@example.com', department: 'IT', status: 'Active' },
    { name: 'Jane Smith', email: 'jane@example.com', department: 'HR', status: 'Inactive' },
    { name: 'Michael Lee', email: 'michael@example.com', department: 'Finance', status: 'Active' },
    { name: 'Sarah Kim', email: 'sarah@example.com', department: 'Operations', status: 'Active' },
    { name: 'David Tan', email: 'david@example.com', department: 'IT', status: 'Inactive' },
    { name: 'Emily Wong', email: 'emily@example.com', department: 'Sales', status: 'Active' }
]
</script>