<script setup>
import { computed, onMounted, ref } from 'vue'
import { Calendar, Droplets, RefreshCw } from 'lucide-vue-next'
import { ApiError, fetchSlots, submitOrder } from './api/client'
import Button from './components/ui/Button.vue'
import SlotGrid from './components/SlotGrid.vue'
import OrderForm from './components/OrderForm.vue'
import ReceiptCard from './components/ReceiptCard.vue'

const step = ref(1) // 1 = Pick Slot, 2 = Details, 3 = Confirmed
const stepTransition = ref('step-forward')

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

const pageTitle = computed(() => {
  if (step.value === 1) return 'Pick a Time'
  if (step.value === 2) return 'Delivery Details'
  return 'All Set'
})

function goToStep(nextStep) {
  stepTransition.value = nextStep >= step.value ? 'step-forward' : 'step-back'
  submitError.value = ''
  step.value = nextStep
}

async function loadSlots(dateOverride = '', isInitial = false) {
  loading.value = true
  loadError.value = ''
  try {
    const data = await fetchSlots(dateOverride)
    minDate.value = data.today

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

    const stillOpen = slots.value.find((s) => s.slot_id === selectedSlotId.value && s.status === 'OPEN')
    if (!stillOpen) {
      const firstOpen = slots.value.find((s) => s.status === 'OPEN')
      selectedSlotId.value = firstOpen ? firstOpen.slot_id : ''
    }
  } catch (err) {
    loadError.value = err.message || 'Unable to load time slots.'
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
  if (step.value === 3) goToStep(1)
  await loadSlots(nextDate, false)
}

async function handleOrderSubmit(payload) {
  submitting.value = true
  submitError.value = ''
  try {
    const data = await submitOrder(payload)
    confirmedOrder.value = data.order
    await loadSlots(selectedDate.value, false)
    goToStep(3)
  } catch (err) {
    if (err instanceof ApiError && (err.code === 'SLOT_FULL' || err.code === 'SLOT_CLOSED')) {
      submitError.value = err.message
      await loadSlots(selectedDate.value, false)
      orderFormRef.value?.regenerateRequestId()
      goToStep(1)
      loadError.value = err.message
    } else if (err instanceof ApiError && err.code === 'DUPLICATE_ORDER') {
      submitError.value = 'This order was already submitted.'
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
  loadError.value = ''
  orderFormRef.value?.regenerateRequestId()
  goToStep(1)
}

onMounted(() => {
  loadSlots('', true)
})
</script>

<template>
  <div class="min-h-screen bg-zinc-50">
    <!-- Ultra-Minimal Glass Header -->
    <header class="sticky top-0 z-20 border-b border-zinc-200/70 bg-white/85 backdrop-blur-md">
      <div class="mx-auto flex max-w-xl items-center justify-between gap-3 px-4 py-3">
        <button
          type="button"
          @click="goToStep(1)"
          class="flex items-center gap-2 cursor-pointer"
        >
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-600 text-white">
            <Droplets class="h-4 w-4" />
          </div>
          <span class="text-base font-bold tracking-tight text-zinc-950">AquaDash</span>
        </button>

        <span class="font-mono text-xs font-medium text-zinc-400">
          Step {{ step }} / 3
        </span>
      </div>
    </header>

    <main class="mx-auto max-w-xl px-4 py-7 sm:py-10">
      <!-- Minimal Step Progress Bar -->
      <div class="mb-5 flex items-center gap-2">
        <div
          v-for="n in 3"
          :key="n"
          class="h-1 flex-1 rounded-full transition-all duration-300"
          :class="n <= step ? 'bg-sky-600' : 'bg-zinc-200'"
        />
      </div>

      <!-- Compact Title + Date Bar -->
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h1 class="text-2xl font-bold tracking-tight text-zinc-950">
          {{ pageTitle }}
        </h1>

        <div v-if="step === 1" class="flex items-center gap-1.5">
          <label
            for="delivery-date"
            class="inline-flex h-9 items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-2.5 text-zinc-700 shadow-2xs transition focus-within:border-sky-500 focus-within:ring-2 focus-within:ring-sky-500/15"
          >
            <Calendar class="h-3.5 w-3.5 text-zinc-400" />
            <input
              id="delivery-date"
              type="date"
              :value="selectedDate"
              :min="minDate"
              @change="handleDateChange"
              class="bg-transparent text-xs font-semibold text-zinc-900 focus:outline-none cursor-pointer"
            />
          </label>

          <Button
            variant="outline"
            size="icon"
            :disabled="loading"
            @click="loadSlots(selectedDate, false)"
            aria-label="Refresh"
          >
            <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': loading }" />
          </Button>
        </div>
      </div>

      <Transition name="fade-slide">
        <div
          v-if="rolledToTomorrow && step === 1"
          class="mb-4 rounded-xl border border-sky-200 bg-sky-50 px-3.5 py-2.5 text-sm font-medium text-sky-900"
        >
          Showing tomorrow's open slots ({{ selectedDate }}).
        </div>
      </Transition>

      <Transition name="fade-slide">
        <div
          v-if="loadError"
          class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm font-medium text-rose-700"
        >
          {{ loadError }}
        </div>
      </Transition>

      <!-- Multi-Step Order Flow -->
      <Transition :name="stepTransition" mode="out-in">
        <SlotGrid
          v-if="step === 1"
          key="step-1"
          :slots="slots"
          :selected-slot-id="selectedSlotId"
          :loading="loading"
          @select="(id) => (selectedSlotId = id)"
          @next="goToStep(2)"
        />

        <OrderForm
          v-else-if="step === 2"
          key="step-2"
          ref="orderFormRef"
          :selected-date="selectedDate"
          :selected-slot="selectedSlot"
          :submitting="submitting"
          :error-message="submitError"
          @back="goToStep(1)"
          @submit="handleOrderSubmit"
        />

        <ReceiptCard
          v-else-if="step === 3 && confirmedOrder"
          key="step-3"
          :order="confirmedOrder"
          @new-order="handleNewOrder"
        />
      </Transition>
    </main>
  </div>
</template>
