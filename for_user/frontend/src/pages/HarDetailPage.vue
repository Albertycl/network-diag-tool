<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <q-btn flat round icon="arrow_back" @click="$router.back()" />
      <h5 class="q-my-none q-ml-sm">Report Details</h5>
    </div>

    <div v-if="loading" class="text-center">
        <q-spinner-dots size="2em" color="primary" />
    </div>

    <div v-else-if="harData">
        <q-banner class="bg-grey-2 q-mb-md rounded-borders">
            <div class="text-subtitle1">Session: <strong>{{ harData.session_uuid }}</strong></div>
            <div class="text-caption">Uploaded: {{ formatToGmt8Manual(harData.created_at) }}</div>
            <div class="text-caption">Total Requests: {{ harData.summary.total }} | Errors: {{ harData.summary.errors }}</div>
        </q-banner>

        <q-table
            :rows="entries"
            :columns="columns"
            row-key="startedDateTime"
            flat
            bordered
            :pagination="initialPagination"
        >
            <template v-slot:body-cell-status="props">
                <q-td :props="props">
                    <q-chip 
                        dense
                        :color="getStatusColor(props.row.response.status)"
                        text-color="white"
                    >
                        {{ props.row.response.status === 0 ? (props.row.response.statusText || 'Error') : props.row.response.status }}
                    </q-chip>
                    <span class="text-caption text-grey q-ml-xs" v-if="props.row.response.status !== 0">{{ props.row.response.statusText }}</span>
                </q-td>
            </template>

            <template v-slot:body-cell-time="props">
                <q-td :props="props">
                    {{ Math.round(props.row.time) }} ms
                </q-td>
            </template>
        </q-table>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const route = useRoute()
const harData = ref(null)
const loading = ref(true)

const BACKEND_URL = ''

const initialPagination = {
    rowsPerPage: 50
}

const columns = [
  { name: 'url', label: 'URL', field: row => row.request.url, align: 'left', sortable: true, style: 'max-width: 400px; overflow: hidden; text-overflow: ellipsis;' },
  { name: 'method', label: 'Method', field: row => row.request.method, align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: row => row.response.status, align: 'left', sortable: true },
  { name: 'time', label: 'Time (ms)', field: 'time', align: 'right', sortable: true },
  { name: 'start', label: 'Start Time', field: 'startedDateTime', align: 'left', format: val => formatToGmt8Manual(val).split(' ')[1] }
]

const entries = computed(() => {
    if (!harData.value || !harData.value.har || !harData.value.har.log) return []
    return harData.value.har.log.entries
})

const fetchHarDetails = async () => {
    loading.value = true
    try {
        const id = route.params.id
        const res = await fetch(`${BACKEND_URL}/api/admin/hars/${id}`)
        if (!res.ok) throw new Error('Failed to load report')
        harData.value = await res.json()
    } catch (e) {
        $q.notify({ type: 'negative', message: e.message })
    } finally {
        loading.value = false
    }
}

const getStatusColor = (status) => {
    if (status === 0) return 'orange' // CORS / Network Error
    if (status >= 200 && status < 300) return 'positive'
    if (status >= 300 && status < 400) return 'info'
    if (status >= 400 && status < 500) return 'warning'
    if (status >= 500) return 'negative'
    return 'grey'
}

const formatToGmt8Manual = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    // Add 8 hours
    const gmt8Time = date.getTime() + (8 * 60 * 60 * 1000)
    const gmt8Date = new Date(gmt8Time)
    
    // Since we shifted the time value itself, we read "UTC" components to get the shifted local time
    const y = gmt8Date.getUTCFullYear()
    const m = String(gmt8Date.getUTCMonth() + 1).padStart(2, '0')
    const d = String(gmt8Date.getUTCDate()).padStart(2, '0')
    const h = String(gmt8Date.getUTCHours()).padStart(2, '0')
    const min = String(gmt8Date.getUTCMinutes()).padStart(2, '0')
    const s = String(gmt8Date.getUTCSeconds()).padStart(2, '0')
    
    return `${y}-${m}-${d} ${h}:${min}:${s}`
}

onMounted(() => {
    fetchHarDetails()
})
</script>
