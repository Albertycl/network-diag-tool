<template>
  <q-page class="flex flex-center column">
    
    <!-- Title Layer: Floating above -->
    <div class="q-mb-xl text-center" style="opacity: 0.8;">
      <h4 class="q-my-none text-weight-regular" style="font-family: serif; color: var(--color-secondary);">
        Diagnosis
      </h4>
      <div class="text-caption text-italic">System Harmony Check</div>
    </div>

    <!-- Main "Strata" Layer -->
    <div class="column q-px-md" style="width: 100%; max-width: 700px;">
      
      <!-- Layer 1: Input -->
      <div class="q-mb-lg bg-surface q-pa-lg shadow-1" style="border-radius: 24px; position: relative; z-index: 2;">
        <q-input 
          v-model="sessionUuid" 
          label="Session UUID" 
          outlined 
          rounded
          dense 
          class="full-width" 
          bg-color="grey-9"
          color="white"
        >
          <template v-slot:prepend>
            <q-icon name="fingerprint" color="secondary" />
          </template>
        </q-input>
      </div>

      <!-- Layer 2: Actions -->
      <div class="row q-col-gutter-md q-mb-xl" style="position: relative; z-index: 1;">
        <div class="col-6">
          <q-btn 
            rounded 
            unelevated
            size="lg"
            color="primary" 
            label="Start Diagnosis" 
            @click="startDiagnosis" 
            :disable="loading" 
            class="full-width"
            icon="play_circle_outline"
          />
        </div>
        <div class="col-6">
          <q-btn 
            rounded 
            unelevated
            size="lg"
            color="secondary" 
            label="Upload Report (Fixed)" 
            icon="cloud_upload" 
            @click="uploadHar" 
            v-if="diagnosisFinished"
            :disable="isUploadDisabled" 
            class="full-width"
            :class="{'upload-flash': uploadHighlight}"
          />
        </div>
      </div>

    <!-- Layer 3: Sediment/Logs -->
      <div v-if="logs.length > 0" class="q-mt-md">
        <div class="text-overline q-ml-sm text-secondary">Trace Logs</div>
        <div class="bg-dark shadow-1 q-pa-md" style="border-radius: 20px;">
          <div v-for="(group, gIndex) in groupedLogs" :key="gIndex" class="q-mb-md">
            <div class="text-subtitle2 text-grey-5 q-mb-sm">{{ group.name }}</div>
            <div class="row q-col-gutter-sm">
              <div v-for="(log, lIndex) in group.items" :key="lIndex" class="col-12 col-sm-6 col-md-4">
                 <div class="row items-center no-wrap q-pa-sm bg-grey-9 rounded-borders">
                    <q-icon :name="log.icon" :color="log.color" size="md" class="q-mr-sm" />
                    <div class="overflow-hidden">
                       <div class="text-weight-bold text-white ellipsis" style="font-size: 0.95em;">{{ log.name }}</div>
                       <div class="text-caption text-orange-3 ellipsis">{{ log.status }}</div>
                    </div>
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="q-mt-md text-center">
        <q-spinner-dots color="primary" size="3em" />
        <div class="text-caption text-secondary">Listening to the network...</div>
      </div>


    </div>

    <!-- Completion Dialog -->
    <q-dialog v-model="showCompletionDialog">
      <q-card style="min-width: 350px; border-radius: 20px;">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6 text-primary">Diagnosis Complete</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md">
          <div class="text-body1">
            Please click the <strong>Upload Report</strong> button to send the results for analysis.
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="OK" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useRoute } from 'vue-router'

const $q = useQuasar()
const route = useRoute()
// Priority: Path Param > Query Param > Empty
const sessionUuid = ref(route.params.session_uuid || route.query.session || '')
const loading = ref(false)
const logs = ref([])
const showCompletionDialog = ref(false)
const uploadHighlight = ref(false)
const diagnosisFinished = ref(false)
const clientInfo = ref(null)

// Dynamic Backend URL
const BACKEND_URL = ''

const groupedLogs = computed(() => {
    const result = []
    let currentClass = null
    let currentGroup = null
    
    // Logs are already sorted by classification in startDiagnosis
    logs.value.forEach(log => {
        const cls = log.classification || 'Unclassified'
        if (cls !== currentClass) {
            currentClass = cls
            currentGroup = { name: cls, items: [] }
            result.push(currentGroup)
        }
        currentGroup.items.push(log)
    })
    return result
})

const startDiagnosis = async () => {
    if (!sessionUuid.value) {
        $q.notify({ type: 'warning', message: 'Please enter a Session UUID' })
        return
    }

    loading.value = true
    logs.value = []
    uploadHighlight.value = false // Reset highlight
    diagnosisFinished.value = false

    try {
        // 0. Fetch Client Info (IP/Location)
        try {
            const ipRes = await fetch('https://api.ip2location.io/')
            if (ipRes.ok) {
                clientInfo.value = await ipRes.json()
            }
        } catch (e) {
            console.warn('Failed to fetch IP info', e)
        }

        // 1. Get Target URLs
        const response = await fetch(`${BACKEND_URL}/api/check-session/${sessionUuid.value}`)
        if (!response.ok) {
             throw new Error('Invalid Session or Expired')
        }
        const data = await response.json()
        let rawUrls = data.target_urls

        // Sort by classification
        rawUrls.sort((a, b) => {
            const c1 = (a.classification || 'Unclassified').toLowerCase()
            const c2 = (b.classification || 'Unclassified').toLowerCase()
            if (c1 < c2) return -1
            if (c1 > c2) return 1
            return 0
        })

        // 2. Iterate and Probe
        for (const item of rawUrls) {
            let name, url, classification
            if (typeof item === 'string') {
                name = item
                url = item
                classification = 'Unclassified'
            } else {
                name = item.name || item.url
                url = item.url
                classification = item.classification || 'Unclassified'
            }
            
            await probeUrl(name, url, classification)
        }

        $q.notify({ type: 'positive', message: 'Diagnosis Completed' })
        showCompletionDialog.value = true
        uploadHighlight.value = true
        diagnosisFinished.value = true

    } catch (e) {
        $q.notify({ type: 'negative', message: e.message })
    } finally {
        loading.value = false
    }
}

const probeUrl = async (name, url, classification) => {
    const startTime = new Date()
    const logItem = { 
        name,
        url,
        classification,
        status: 'Pending', 
        icon: 'hourglass_empty', 
        color: 'grey',
        startedDateTime: startTime.toISOString(),
        time: 0,
        status_code: 0,
        status_text: ''
    }
    logs.value.push(logItem)
    
    let status_code = 0
    let error_message = null
    let finalStatusDisplay = ''
    let icon = ''
    let color = ''

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)

    try {
        console.log(`Probing ${url} ...`)
        const res = await fetch(url, { 
            method: 'GET',
            signal: controller.signal
            // removed mode: 'no-cors' and redirect: 'manual' to ensure browser network visibility
            // This means requests to google.com WILL fail with CORS in the console,
            // BUT they will appear in the Network tab (as failed/red).
        })
        
        // If we reach here, we got a response (200-299 or even 404/500 if CORS allowed).
        status_code = res.status
        finalStatusDisplay = `Status: ${res.status}`
        icon = 'check_circle'
        color = 'positive'

        logItem.status_text = res.statusText

    } catch (error) {
        console.error(`Probe failed for ${url}:`, error)
        if (error.name === 'AbortError') {
            status_code = 0 
            finalStatusDisplay = 'Timeout'
            icon = 'timer_off'
            color = 'negative'
            error_message = 'Request timed out after 10 seconds'
        } else {
            // It failed. Now we play detective.
            // Try again with mode: 'no-cors'
            // If this "succeeds" (returns opaque), it means the server IS there, so it was CORS.
            // If this fails, it means the server is NOT there (Network Error).
            try {
                await fetch(url, { 
                    method: 'GET', 
                    mode: 'no-cors',
                    signal: AbortSignal.timeout(5000) // 5s timeout for this check
                })
                
                // If we get here, the server is reachable!
                status_code = 0
                finalStatusDisplay = 'CORS Error'
                icon = 'gpp_bad' // Shield/Security icon
                color = 'orange'
                error_message = 'Blocked by CORS Policy (Server is reachable)'

            } catch (probeError) {
                // If the no-cors request ALSO fails, the server is likely down/unreachable
                status_code = 0
                finalStatusDisplay = 'Network Error'
                icon = 'wifi_off'
                color = 'red'
                error_message = 'Network Unreachable (DNS/Connection Failed)'
            }
        }
        // Use the short label (CORS Error, Timeout, Network Error) for the HAR/UI list
        logItem.status_text = finalStatusDisplay || 'Failed'
    } finally {
        clearTimeout(timeoutId)
        const endTime = new Date()
        logItem.time = endTime - startTime
    }
    
    // Update UI
    logItem.status = finalStatusDisplay
    logItem.icon = icon
    logItem.color = color
    logItem.status_code = status_code

    // 3. Report back
    try {
        await fetch(`${BACKEND_URL}/api/submit-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_uuid: sessionUuid.value,
                url: url,
                status_code: status_code === 0 ? finalStatusDisplay : status_code,
                error_message: error_message,
                client_info: clientInfo.value
            })
        })
    } catch (reportError) {
        console.error("Failed to submit report", reportError)
        $q.notify({ type: 'negative', message: 'Failed to submit report for ' + url })
    }
}

const uploadHar = async () => {
    if (loading.value) return
    loading.value = true
    const entries = logs.value.map(log => {
        return {
            startedDateTime: log.startedDateTime,
            time: log.time,
            request: {
                method: 'GET',
                url: log.url,
                httpVersion: 'HTTP/1.1',
                cookies: [],
                headers: [],
                queryString: [],
                headersSize: -1,
                bodySize: -1
            },
            response: {
                status: typeof log.status_code === 'number' ? log.status_code : 0,
                statusText: log.status_text || '',
                httpVersion: 'HTTP/1.1',
                cookies: [],
                headers: [],
                content: {
                    size: -1,
                    mimeType: 'x-unknown'
                },
                redirectURL: '',
                headersSize: -1,
                bodySize: -1
            },
            cache: {},
            timings: {
                send: 0,
                wait: log.time,
                receive: 0
            },
            _classification: log.classification
        }
    })

    const har = {
        log: {
            version: '1.2',
            creator: {
                name: 'Network Diagnostic Tool',
                version: '1.0'
            },
            pages: [],
            entries: entries
        }
    }

    try {
        const res = await fetch(`${BACKEND_URL}/api/upload-har`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_uuid: sessionUuid.value,
                har: har
            })
        })
        
        if (!res.ok) throw new Error('Upload failed')
        const data = await res.json()
        
        $q.notify({ 
            type: 'positive', 
            message: `Report Uploaded! (ID: ${data.id})`,
            caption: `Errors: ${data.summary.errors} | Avg Time: ${data.summary.avg_time}ms`
        })
        uploadHighlight.value = false // Stop flashing on success

    } catch (e) {
        $q.notify({ type: 'negative', message: 'Upload Failed: ' + e.message })
    } finally {
        loading.value = false
    }
}

const isUploadDisabled = computed(() => {
    return logs.value.length === 0 || loading.value
})

</script>

<style>
@keyframes flash-btn {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.7; box-shadow: 0 0 15px rgba(0,0,0,0.2); }
  100% { transform: scale(1); opacity: 1; }
}

.upload-flash {
  animation: flash-btn 1s infinite ease-in-out;
  border: 2px solid #26A69A; /* Ensure border helps visibility */
  z-index: 10;
}
</style>
