<script setup>
import { computed, onMounted, ref } from 'vue'
import { ApiError, fetchSlots, submitOrder } from './api/client'
import SlotGrid from './components/SlotGrid.vue'
import OrderForm from './components/OrderForm.vue'
import ReceiptCard from './components/ReceiptCard.vue'
import OwnerCapacityView from './components/OwnerCapacityView.vue'

const activeTab = ref(window.location.hash === '#/capacity' ? 'capacity' : 'order')
const selectedDate = ref('')
const minDate = ref('')
const rolledToTomorrow = ref(false)
const slots = ref([])
const selectedSlotId = ref('')
const loading = ref(false)
const loadError = ref('')

const submitting = ref(false)
const submitError = ref('')
const confirmedOrder = ref(null)
const orderFormRef = ref(null)

const selectedSlot = computed(() =>
  slots.value.find((s) => s.slot_id === selectedSlotId.value && s.status === 'OPEN') || null,
)

function setTab(tab) {
  activeTab.value = tab
  window.location.hash = tab === 'capacity' ? '#/capacity' : '#/'
}

async function loadSlots(dateOverride = '', isInitial = false) {
  loading.value = true
  loadError.value = ''
  try {
    const data = await fetchSlots(dateOverride)
    minDate.value = data.today

    // On initial page open after 19:00 PHT, automatically show tomorrow's open slots
    if (isInitial && !dateOverride && data.all_today_closed && data.default_date !== data.date) {
      rolledToTomorrow.value = true
      selectedDate.value = data.default_date
      const tomorrowData = await fetchSlots(data.default_date)
      slots.value = tomorrowData.slots
    } else {
      if (dateOverride && dateOverride === data.today) {
        rolledToTomorrow.value = false
      }
      selectedDate.value = data.date
      slots.value = data.slots
    }

    // Keep selected slot if still open, otherwise auto-pick first open slot
    const stillOpen = slots.value.find((s) => s.slot_id === selectedSlotId.value && s.status === 'OPEN')
    if (!stillOpen) {
      const firstOpen = slots.value.find((s) => s.status === 'OPEN')
      selectedSlotId.value = firstOpen ? firstOpen.slot_id : ''
    }
  } catch (err) {
    loadError.value = err.message || 'Could not load time slots from the server.'
  } finally {
    loading.value = false
  }
}

async function handleDateChange(event) {
  const nextDate = event.target.value
  if (!nextDate) return
  rolledToTomorrow.value = false
  confirmedOrder.value = null
  submitError.value = ''
  await loadSlots(nextDate, false)
}

async function handleOrderSubmit(payload) {
  submitting.value = true
  submitError.value = ''
  try {
    const data = await submitOrder(payload)
    confirmedOrder.value = data.order
    await loadSlots(selectedDate.value, false)
  } catch (err) {
    if (err instanceof ApiError && (err.code === 'SLOT_FULL' || err.code === 'SLOT_CLOSED')) {
      submitError.value = err.message
      await loadSlots(selectedDate.value, false)
      orderFormRef.value?.regenerateRequestId()
    } else if (err instanceof ApiError && err.code === 'DUPLICATE_ORDER') {
      submitError.value = 'This order was already submitted. Refreshing slot availability...'
      await loadSlots(selectedDate.value, false)
      orderFormRef.value?.regenerateRequestId()
    } else {
      submitError.value = err.message || 'Unable to place order right now.'
      orderFormRef.value?.regenerateRequestId()
    }
  } finally {
    submitting.value = false
  }
}

function handleNewOrder() {
  confirmedOrder.value = null
  submitError.value = ''
  orderFormRef.value?.regenerateRequestId()
}

onMounted(() => {
  loadSlots('', true)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-4 py-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-600 text-lg font-bold text-white shadow-sm">
            💧
          </div>
          <div>
            <h1 class="text-xl font-bold tracking-tight text-slate-900">AquaDash</h1>
            <p class="text-xs text-slate-500">Subdivision 5-Gallon Water Refill Delivery</p>
          </div>
        </div>

        <nav class="flex items-center gap-1 rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            @click="setTab('order')"
            class="rounded-lg px-3.5 py-1.5 text-sm font-semibold transition cursor-pointer"
            :class="activeTab === 'order' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            Order Refill
          </button>
          <button
            type="button"
            @click="setTab('capacity')"
            class="rounded-lg px-3.5 py-1.5 text-sm font-semibold transition cursor-pointer"
            :class="activeTab === 'capacity' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          >
            Slot Capacity (Owner)
          </button>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-5xl space-y-5 px-4 py-6">
      <div class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-xs">
        <div class="flex flex-wrap items-center gap-3">
          <label for="delivery-date" class="text-sm font-medium text-slate-700">Delivery Date (PHT):</label>
          <input
            id="delivery-date"
            type="date"
            :value="selectedDate"
            :min="activeTab === 'order' ? minDate : undefined"
            @change="handleDateChange"
            class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-900 focus:border-sky-500 focus:outline-none"
          />
        </div>

        <button
          type="button"
          @click="loadSlots(selectedDate, false)"
          :disabled="loading"
          class="rounded-lg border border-slate-300 bg-white px-3.5 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50 cursor-pointer"
        >
          {{ loading ? 'Refreshing...' : 'Refresh Slots' }}
        </button>
      </div>

      <div
        v-if="rolledToTomorrow && activeTab === 'order'"
        class="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900"
      >
        Today's delivery windows have ended (past 7:00 PM PHT) — showing tomorrow's open slots ({{ selectedDate }}).
      </div>

      <div
        v-if="loadError"
        class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        {{ loadError }}
      </div>

      <template v-if="activeTab === 'order'">
        <ReceiptCard
          v-if="confirmedOrder"
          :order="confirmedOrder"
          @new-order="handleNewOrder"
        />

        <template v-else>
          <SlotGrid
            :slots="slots"
            :selected-slot-id="selectedSlotId"
            :loading="loading"
            @select="(id) => (selectedSlotId = id)"
          />

          <OrderForm
            ref="orderFormRef"
            :selected-date="selectedDate"
            :selected-slot="selectedSlot"
            :submitting="submitting"
            :error-message="submitError"
            @submit="handleOrderSubmit"
          />
        </template>
      </template>

      <OwnerCapacityView
        v-else
        :selected-date="selectedDate"
        :slots="slots"
        :loading="loading"
      />
    </main>

    <footer class="mx-auto max-w-5xl px-4 py-6 text-center text-xs text-slate-400">
      AquaDash • Group bcsad-g02 • Case 9 Water Refilling Station Orders
    </footer>
  </div>
</template>
