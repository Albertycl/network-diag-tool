<template>
  <q-page class="q-pa-md">
    <div class="row justify-between items-center q-mb-md">
      <h5 class="q-my-none">Admin: HAR Reports</h5>
      <q-btn flat icon="refresh" @click="fetchHars" />
    </div>

    <q-banner class="bg-grey-9 text-white q-mb-md rounded-borders">
        <template v-slot:avatar>
            <q-icon name="info" color="orange" />
        </template>
        Note: The request timeout is set to <strong>10 seconds</strong>.
    </q-banner>

    <q-table
      :rows="hars"
      :columns="columns"
      row-key="id"
      :loading="loading"
      flat
      bordered
    >
        <template v-slot:body-cell-session_uuid="props">
            <q-td :props="props">
                <span style="font-family: monospace; font-size: 1.1em; letter-spacing: 0.5px;">{{ props.row.session_uuid }}</span>
            </q-td>
        </template>
        


        <template v-slot:body-cell-created_at="props">
            <q-td :props="props">
                {{ formatToGmt8Manual(props.row.created_at) }}
            </q-td>
        </template>

        <template v-slot:body-cell-summary="props">
            <q-td :props="props">
                <div class="row q-gutter-sm">
                    <q-chip 
                        v-for="(count, status) in props.row.summary.status_counts" 
                        :key="status"
                        dense
                        :color="getStatusColor(status)"
                        text-color="white"
                    >
                        {{ status }}: {{ count }}
                    </q-chip>
                </div>
                <div class="text-caption text-grey">
                    Avg Time: {{ props.row.summary.avg_time }}ms | Total: {{ props.row.summary.total }}
                </div>
            </q-td>
        </template>

        <template v-slot:body-cell-actions="props">
            <q-td :props="props">
                <q-btn flat dense icon="visibility" color="primary" @click="$router.push(`/admin/hars/${props.row.id}`)" title="View Details" />
                <q-btn flat dense icon="download" color="primary" @click="downloadOriginal(props.row)" title="Download JSON" />
            </q-td>
        </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const hars = ref([])
const loading = ref(false)

const BACKEND_URL = ''

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left', sortable: true, style: 'width: 50px' },
  { name: 'session_uuid', label: 'Session UUID', field: 'session_uuid', align: 'left', sortable: true },
  { name: 'created_at', label: 'Uploaded At (GMT+8)', field: 'created_at', align: 'left', sortable: true },
  { name: 'summary', label: 'Analysis (Status Counts)', field: 'summary', align: 'left' },
  { name: 'actions', label: 'Actions', field: 'actions', align: 'center' }
]

const fetchHars = async () => {
    loading.value = true
    try {
        const res = await fetch(`${BACKEND_URL}/api/admin/hars`)
        if (!res.ok) throw new Error('Failed to fetch reports')
        hars.value = await res.json()
    } catch (e) {
        $q.notify({ type: 'negative', message: e.message })
    } finally {
        loading.value = false
    }
}

const formatToGmt8 = (dateStr) => {
    if (!dateStr) return ''
    // Backend sends naive UTC string e.g. "2023-01-01T12:00:00"
    // Treat it as UTC
    const date = new Date(dateStr + 'Z')
    
    // Format to GMT+8
    // We can use Intl.DateTimeFormat with timeZone: 'Asia/Shanghai' (which is GMT+8)
    return new Intl.DateTimeFormat('en-GB', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false,
        timeZone: 'Asia/Shanghai'
    }).format(date).replace(/\//g, '-') 
    // en-GB gives dd/mm/yyyy. We might want yyyy-mm-dd. 
    // Let's manually do it to be safe and consistent with screenshot style
}

// Manual formatter for strict control
const formatToGmt8Manual = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr + 'Z')
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

const getStatusColor = (status) => {
    if (status === 'CORS/Network Error') return 'orange'
    const code = parseInt(status)
    if (code >= 200 && code < 300) return 'positive'
    if (code >= 300 && code < 400) return 'info'
    if (code >= 400 && code < 500) return 'warning'
    if (code >= 500) return 'negative'
    return 'grey'
}

const downloadOriginal = async (row) => {
    // We need to fetch details to get the full HAR content if it's large and not in listing
    // But listing might not have it. Let's assume listing has summary only.
    // Wait, backend list_hars does NOT return har_content. Good.
    try {
        const res = await fetch(`${BACKEND_URL}/api/admin/hars/${row.id}`)
        if (!res.ok) throw new Error('Fetch failed')
        const data = await res.json()
        
        const blob = new Blob([JSON.stringify(data.har, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `report_${row.id}_${row.session_uuid}.har`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    } catch (e) {
        $q.notify({ type: 'negative', message: 'Download failed: ' + e.message })
    }
}

onMounted(() => {
    fetchHars()
})
</script>
