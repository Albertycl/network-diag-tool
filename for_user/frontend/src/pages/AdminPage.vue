<template>
  <q-page class="q-pa-md">
    <div class="row justify-between items-center q-mb-md">
      <h5 class="q-my-none">Admin: Active Sessions</h5>
      <div>
          <q-btn color="primary" label="Create Session" icon="add" @click="openCreate" class="q-mr-sm" />
          <q-btn flat icon="refresh" @click="fetchSessions" />
      </div>
    </div>

    <q-table
      :rows="sessions"
      :columns="columns"
      row-key="session_uuid"
      :loading="loading"
      flat
      bordered
    >
      <template v-slot:body-cell-session_uuid="props">
        <q-td :props="props">
          <span style="font-family: monospace; font-size: 1.1em; letter-spacing: 0.5px;">{{ props.row.session_uuid }}</span>
        </q-td>
      </template>

      <template v-slot:body-cell-expires_at="props">
        <q-td :props="props">
            <q-chip :color="getExpirationColor(props.row.expires_at)" text-color="white" dense>
                {{ formatExpiration(props.row.expires_at) }}
            </q-chip>
        </q-td>
      </template>

      <template v-slot:body-cell-actions="props">
        <q-td :props="props">
            <q-btn flat dense icon="content_copy" color="primary" @click="copyUuid(props.row.session_uuid)" title="Copy UUID" />
            <q-btn flat dense icon="edit" color="blue" @click="openEdit(props.row)" title="Edit" />
            <q-btn flat dense icon="delete" color="negative" @click="deleteSession(props.row.session_uuid)" title="Delete" />
            <q-btn flat dense icon="play_arrow" color="green" label="Use" @click="useSession(props.row.session_uuid)" />
        </q-td>
      </template>

      <template v-slot:body-cell-target_urls="props">
        <q-td :props="props">
          <div style="white-space: pre-wrap; word-break: break-all;">
            {{ props.row.target_urls.length }} URLs
          </div>
        </q-td>
      </template>
    </q-table>

    <!-- Create/Edit Dialog -->
    <q-dialog v-model="showDialog" persistent>
      <q-card style="min-width: 1200px">
        <q-card-section>
          <div class="text-h6">{{ isEdit ? 'Edit Session' : 'New Session' }}</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <div v-if="!isEdit" class="q-mb-md">
             <q-input v-model.number="editingSession.expires_in_hours" type="number" label="Expires In (Hours)" outlined />
          </div>

          <div class="text-subtitle2 q-mb-sm">Target URLs</div>
          <div v-for="(target, index) in editingTargets" :key="index" class="row q-col-gutter-sm q-mb-sm items-center">
              <div class="col-2">
                  <q-input v-model="target.classification" label="Classification" outlined dense hide-bottom-space />
              </div>
              <div class="col-3">
                  <q-input v-model="target.name" label="Display Name" outlined dense hide-bottom-space />
              </div>
              <div class="col-4">
                   <q-input v-model="target.url" label="URL" outlined dense :rules="[val => !!val || 'Required']" hide-bottom-space />
              </div>
              <div class="col-2">
                  <q-input v-model="target.checking_which_content" label="Checking Content" outlined dense hide-bottom-space />
              </div>
              <div class="col-1">
                  <q-btn flat dense icon="delete" color="negative" @click="removeTarget(index)" />
              </div>
          </div>
          <q-btn flat label="+ Add Target" color="primary" @click="addTarget" />

        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn flat label="Save" color="primary" @click="saveSession" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { copyToClipboard, useQuasar } from 'quasar'

const $q = useQuasar()
const router = useRouter()
const sessions = ref([])
const loading = ref(false)

// Dialog State
const showDialog = ref(false)
const isEdit = ref(false)

const editingSession = ref({
    session_uuid: '',
    expires_in_hours: 1
})
const editingTargets = ref([])

const BACKEND_URL = ''

const columns = [
  { name: 'session_uuid', label: 'Session UUID', field: 'session_uuid', align: 'left', sortable: true },
  { name: 'expires_at', label: 'Expires At (UTC)', field: 'expires_at', align: 'left', sortable: true },
  { name: 'url_count', label: 'Targets', field: row => row.target_urls.length, align: 'center' },
  { name: 'actions', label: 'Actions', field: 'actions', align: 'center' }
]

const fetchSessions = async () => {
    loading.value = true
    try {
        const res = await fetch(`${BACKEND_URL}/api/admin/sessions`)
        if (!res.ok) throw new Error('Failed to fetch')
        sessions.value = await res.json()
    } catch (e) {
        $q.notify({ type: 'negative', message: e.message })
    } finally {
        loading.value = false
    }
}

const DEFAULT_TEMPLATE = [
  { classification: 'Search', name: 'Google', url: 'https://www.google.com', checking_which_content: '' },
  { classification: 'Demo', name: 'Example', url: 'https://www.example.com', checking_which_content: 'Example Domain' },
  { classification: 'Code', name: 'GitHub', url: 'https://github.com', checking_which_content: '' },
  { classification: 'CDN', name: 'Cloudflare', url: 'https://www.cloudflare.com', checking_which_content: '' },
  { classification: 'API', name: 'GitHub API', url: 'https://api.github.com', checking_which_content: '' }
]

const openCreate = () => {
    isEdit.value = false
    editingSession.value = { expires_in_hours: 1 }
    // Deep copy to avoid reference issues
    editingTargets.value = JSON.parse(JSON.stringify(DEFAULT_TEMPLATE))
    showDialog.value = true
}

const openEdit = (session) => {
    isEdit.value = true
    editingSession.value = { ...session }
    
    // Parse targets: handle both strings (legacy) and objects
    editingTargets.value = session.target_urls.map(t => {
        if (typeof t === 'string') {
            return { name: t, url: t }
        }
        return { 
            name: t.name || t.url, 
            url: t.url,
            classification: t.classification || '',
            checking_which_content: t.checking_which_content || ''
        }
    })
    
    showDialog.value = true
}

const addTarget = () => {
    editingTargets.value.push({ name: '', url: '', classification: '', checking_which_content: '' })
}

const removeTarget = (index) => {
    editingTargets.value.splice(index, 1)
}

const saveSession = async () => {
    // Validate
    const targets = editingTargets.value.filter(t => t.url.trim())
    if (targets.length === 0) {
        $q.notify({ type: 'warning', message: 'Add at least one target URL' })
        return
    }

    const payload = {
        target_urls: targets, // Send structured list
        expires_in_hours: editingSession.value.expires_in_hours
    }

    try {
        let url = `${BACKEND_URL}/api/admin/sessions`
        let method = 'POST'
        
        if (isEdit.value) {
            url += `/${editingSession.value.session_uuid}`
            method = 'PUT'
        }

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })

        if (!res.ok) throw new Error('Save failed')
        
        showDialog.value = false
        fetchSessions()
        $q.notify({ type: 'positive', message: 'Session Saved' })

    } catch (e) {
        $q.notify({ type: 'negative', message: e.message })
    }
}

const deleteSession = async (uuid) => {
    if (!confirm('Are you sure you want to delete this session?')) return

    try {
        const res = await fetch(`${BACKEND_URL}/api/admin/sessions/${uuid}`, { method: 'DELETE' })
        if (!res.ok) throw new Error('Failed to delete session')
        $q.notify({ type: 'positive', message: 'Session Deleted' })
        fetchSessions()
    } catch (e) {
        $q.notify({ type: 'negative', message: e.message })
    }
}

const copyUuid = (uuid) => {
    copyToClipboard(uuid)
        .then(() => {
            $q.notify({ type: 'positive', message: 'UUID Copied!' })
        })
        .catch(() => {
            $q.notify({ type: 'negative', message: 'Failed to copy' })
        })
}

const useSession = (uuid) => {
    router.push({ path: `/${uuid}` })
}

const getExpirationColor = (dateStr) => {
    const now = new Date()
    // Explicitly treat the string from backend as GMT+8
    const expiry = new Date(dateStr + '+08:00') 
    if (now > expiry) return 'grey'
    
    // Warning if less than 30 mins
    const diffMs = expiry - now
    if (diffMs < 30 * 60 * 1000) return 'orange'
    
    return 'positive'
}

const formatExpiration = (dateStr) => {
    const now = new Date()
    const expiry = new Date(dateStr + '+08:00') // GMT+8
    
    if (now > expiry) {
        return 'Expired'
    }
    
    const diffMs = expiry - now
    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    
    if (diffHrs > 24) {
      const days = Math.floor(diffHrs / 24)
      return `${days}d remaining`
    }
    
    if (diffHrs > 0) {
        return `in ${diffHrs}h ${diffMins}m`
    }
    
    return `in ${diffMins}m`
}

onMounted(() => {
    fetchSessions()
})
</script>
