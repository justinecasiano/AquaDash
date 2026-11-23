<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  selectedDate: {
    type: String,
    required: true,
  },
  selectedSlot: {
    type: Object,
    default: null,
  },
  submitting: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['submit'])

function makeRequestId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID().replace(/-/g, '').slice(0, 20)
  }
  return `req_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
}

const form = reactive({
  customer_name: '',
  address: '',
  phone: '',
  quantity: 2,
  notes: '',
})

const clientRequestId = ref(makeRequestId())
const localError = ref('')

// Fresh idempotency ID whenever the user changes slot/date after a conflict
watch(
  () => [props.selectedDate, props.selectedSlot?.slot_id],
  () => {
    clientRequestId.value = makeRequestId()
    localError.value = ''
  },
)

function adjustQty(delta) {
  const next = form.quantity + delta
  if (next >= 1 && next <= 20) {
    form.quantity = next
  }
}

function handleSubmit() {
  localError.value = ''

  if (!props.selectedSlot) {
    localError.value = 'Please choose an open delivery time slot first.'
    return
  }
  if (form.customer_name.trim().length < 2) {
    localError.value = 'Please enter your name (at least 2 characters).'
    return
  }
  if (form.address.trim().length < 5) {
    localError.value = 'Please enter your subdivision home address (Block, Lot, Street).'
    return
  }
  if (form.phone.trim().length < 7) {
    localError.value = 'Please enter a valid mobile or landline number.'
    return
  }

  emit('submit', {
    date: props.selectedDate,
    slot_id: props.selectedSlot.slot_id,
    customer_name: form.customer_name.trim(),
    address: form.address.trim(),
    phone: form.phone.trim(),
    quantity: Number(form.quantity),
    notes: form.notes.trim(),
    client_request_id: clientRequestId.value,
  })
}

function regenerateRequestId() {
  clientRequestId.value = makeRequestId()
}

defineExpose({ regenerateRequestId })
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">2. Enter Delivery Details</h2>
        <p class="text-sm text-slate-500">Order 5-gallon purified water refill containers for your household.</p>
      </div>
      <div
        v-if="selectedSlot"
        class="inline-flex items-center gap-1.5 rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-800"
      >
        <span>Selected:</span>
        <span>{{ selectedDate }} • {{ selectedSlot.label }}</span>
      </div>
    </div>

    <div
      class="mb-5 flex items-start gap-2.5 rounded-xl border border-sky-200 bg-sky-50/70 px-3.5 py-2.5 text-xs text-sky-900"
    >
      <span class="mt-0.5 font-bold text-sky-700">Privacy:</span>
      <p>
        Your home address and contact number are private. They are sent over HTTPS and shown only to our authenticated delivery rider — never on public pages.
      </p>
    </div>

    <div
      v-if="localError || errorMessage"
      class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
    >
      {{ localError || errorMessage }}
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label for="customer_name" class="mb-1 block text-sm font-medium text-slate-700">
            Household / Customer Name <span class="text-rose-500">*</span>
          </label>
          <input
            id="customer_name"
            v-model="form.customer_name"
            type="text"
            maxlength="100"
            required
            placeholder="e.g., Maria Santos"
            class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 focus:outline-none"
          />
        </div>

        <div>
          <label for="phone" class="mb-1 block text-sm font-medium text-slate-700">
            Contact Number <span class="text-rose-500">*</span>
          </label>
          <input
            id="phone"
            v-model="form.phone"
            type="tel"
            maxlength="20"
            required
            placeholder="e.g., 0917 123 4567"
            class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 focus:outline-none"
          />
        </div>
      </div>

      <div>
        <label for="address" class="mb-1 block text-sm font-medium text-slate-700">
          Subdivision Home Address (Private) <span class="text-rose-500">*</span>
        </label>
        <input
          id="address"
          v-model="form.address"
          type="text"
          maxlength="300"
          required
          placeholder="e.g., Blk 4 Lot 12 Sampaguita St, Phase 2"
          class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 focus:outline-none"
        />
      </div>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">
            5-Gallon Containers <span class="text-rose-500">*</span>
          </label>
          <div class="inline-flex items-center rounded-xl border border-slate-300 bg-white">
            <button
              type="button"
              @click="adjustQty(-1)"
              :disabled="form.quantity <= 1"
              class="px-4 py-2 text-lg font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-40 cursor-pointer rounded-l-xl"
            >
              −
            </button>
            <span class="min-w-[3.5rem] text-center text-base font-bold text-slate-900">
              {{ form.quantity }}
            </span>
            <button
              type="button"
              @click="adjustQty(1)"
              :disabled="form.quantity >= 20"
              class="px-4 py-2 text-lg font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-40 cursor-pointer rounded-r-xl"
            >
              +
            </button>
          </div>
          <p class="mt-1 text-xs text-slate-500">1 to 20 containers per order.</p>
        </div>

        <div>
          <label for="notes" class="mb-1 block text-sm font-medium text-slate-700">
            Delivery Notes (Optional)
          </label>
          <input
            id="notes"
            v-model="form.notes"
            type="text"
            maxlength="250"
            placeholder="e.g., Green gate, leave by garage"
            class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 focus:outline-none"
          />
        </div>
      </div>

      <div class="pt-2">
        <button
          type="submit"
          :disabled="submitting || !selectedSlot"
          class="w-full rounded-xl bg-sky-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-auto cursor-pointer"
        >
          {{ submitting ? 'Submitting Order...' : 'Place Water Refill Order' }}
        </button>
      </div>
    </form>
  </section>
</template>
