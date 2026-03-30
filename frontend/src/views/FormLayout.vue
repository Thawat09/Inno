<template>
    <section class="page-section">
        <div class="single-grid">
            <Card class="content-card">
                <template #title>Form Layout</template>
                <template #content>
                    <div class="form-grid">
                        <div class="form-field">
                            <label>Full Name</label>
                            <InputText placeholder="Enter full name" />
                        </div>

                        <div class="form-field">
                            <label>Email</label>
                            <InputText placeholder="Enter email" />
                        </div>

                        <div class="form-field">
                            <label>Phone</label>
                            <InputText placeholder="Enter phone number" />
                        </div>

                        <div class="form-field">
                            <label>Department</label>
                            <Dropdown :options="departments" optionLabel="name" placeholder="Select department" />
                        </div>

                        <div class="form-field form-field-full">
                            <label>Address</label>
                            <Textarea rows="4" placeholder="Enter address" />
                        </div>

                        <div class="form-actions">
                            <Button label="Save" icon="pi pi-check" />
                            <Button label="Cancel" icon="pi pi-times" outlined />
                        </div>
                    </div>
                </template>
            </Card>
        </div>
    </section>
</template>

<script setup>
const departments = [
    { name: 'IT' },
    { name: 'Finance' },
    { name: 'HR' },
    { name: 'Operations' }
]
</script>