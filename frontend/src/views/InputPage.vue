<template>
    <section class="page-section">
        <div class="single-grid">
            <Card class="content-card">
                <template #title>Input Demo</template>
                <template #content>
                    <div class="form-grid">
                        <div class="form-field">
                            <label>Username</label>
                            <InputText v-model="form.username" placeholder="Username" />
                        </div>

                        <div class="form-field">
                            <label>Salary</label>
                            <InputNumber v-model="form.salary" mode="currency" currency="USD" locale="en-US" />
                        </div>

                        <div class="form-field form-field-full">
                            <label>Description</label>
                            <Textarea v-model="form.description" rows="5" />
                        </div>

                        <div class="form-actions">
                            <Button label="Submit" icon="pi pi-send" />
                        </div>
                    </div>

                    <div class="preview-box">
                        <h3>Preview</h3>
                        <p><strong>Username:</strong> {{ form.username }}</p>
                        <p><strong>Salary:</strong> {{ form.salary }}</p>
                        <p><strong>Description:</strong> {{ form.description }}</p>
                    </div>
                </template>
            </Card>
        </div>
    </section>
</template>

<script setup>
import { reactive } from 'vue'

const form = reactive({
    username: '',
    salary: null,
    description: ''
})
</script>