<script setup>
import { computed, onMounted, ref } from 'vue'
import { BarChart3, Calendar, Droplets, RefreshCw, ShoppingBag } from 'lucide-vue-next'
import { ApiError, fetchSlots, submitOrder } from './api/client'
import Button from './components/ui/Button.vue'
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
  orderFormRef.value?.regenerateRequestId()
}

onMounted(() => {
  loadSlots('', true)
})
</script>

<template>
  <div class="min-h-screen bg-zinc-50">
    <!-- Minimalist Glass Header -->
    <header class="sticky top-0 z-20 border-b border-zinc-200/80 bg-white/85 backdrop-blur-md">
      <div class="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
        <div class="flex items-center gap-2.5">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-600 text-white shadow-xs">
            <Droplets class="h-5 w-5" />
          </div>
          <span class="text-xl font-bold tracking-tight text-zinc-950">AquaDash</span>
        </div>

        <!-- shadcn Segmented Tabs -->
        <nav class="inline-flex items-center rounded-xl border border-zinc-200/80 bg-zinc-100/90 p-1">
          <button
            type="button"
            @click="setTab('order')"
            class="inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-semibold transition-all duration-150 cursor-pointer"
            :class="
              activeTab === 'order'
                ? 'bg-white text-zinc-950 shadow-xs'
                : 'text-zinc-500 hover:text-zinc-900'
            "
          >
            <ShoppingBag class="h-4 w-4" />
            <span>Order</span>
          </button>
          <button
            type="button"
            @click="setTab('capacity')"
            class="inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-semibold transition-all duration-150 cursor-pointer"
            :class="
              activeTab === 'capacity'
                ? 'bg-white text-zinc-950 shadow-xs'
                : 'text-zinc-500 hover:text-zinc-900'
            "
          >
            <BarChart3 class="h-4 w-4" />
            <span>Capacity</span>
          </button>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-4xl space-y-7 px-4 py-7 sm:px-6 sm:py-9">
      <!-- Clean Hero + Compact Date Controls -->
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-tight text-zinc-950">
            {{ activeTab === 'order' ? 'Water Refill Delivery' : 'Slot Capacity' }}
          </h1>
          <p class="mt-1 text-base text-zinc-500">
            {{ activeTab === 'order' ? '5-gallon purified water delivered to your door.' : 'Live daily slot fullness overview.' }}
          </p>
        </div>

        <div class="flex items-center gap-2">
          <label
            for="delivery-date"
            class="inline-flex h-11 items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3.5 text-sm font-medium text-zinc-700 shadow-2xs transition focus-within:border-sky-500 focus-within:ring-3 focus-within:ring-sky-500/15"
          >
            <Calendar class="h-4 w-4 text-zinc-400" />
            <input
              id="delivery-date"
              type="date"
              :value="selectedDate"
              :min="activeTab === 'order' ? minDate : undefined"
              @change="handleDateChange"
              class="bg-transparent text-base font-semibold text-zinc-950 focus:outline-none cursor-pointer"
            />
          </label>

          <Button
            variant="outline"
            size="icon"
            class="h-11 w-11"
            :disabled="loading"
            @click="loadSlots(selectedDate, false)"
            aria-label="Refresh slots"
          >
            <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
          </Button>
        </div>
      </div>

      <Transition name="fade-slide">
        <div
          v-if="rolledToTomorrow && activeTab === 'order'"
          class="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-base font-medium text-sky-900"
        >
          Today's slots have ended — showing tomorrow ({{ selectedDate }}).
        </div>
      </Transition>

      <Transition name="fade-slide">
        <div
          v-if="loadError"
          class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-base font-medium text-rose-700"
        >
          {{ loadError }}
        </div>
      </Transition>

      <Transition name="fade-slide" mode="out-in">
        <div v-if="activeTab === 'order'" key="order-view" class="space-y-8">
          <Transition name="fade-slide" mode="out-in">
            <ReceiptCard
              v-if="confirmedOrder"
              key="receipt"
              :order="confirmedOrder"
              @new-order="handleNewOrder"
            />

            <div v-else key="form" class="space-y-8">
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
            </div>
          </Transition>
        </div>

        <OwnerCapacityView
          v-else
          key="capacity-view"
          :selected-date="selectedDate"
          :slots="slots"
          :loading="loading"
        />
      </Transition>
    </main>
  </div>
</template>
