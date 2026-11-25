<script setup>
import { reactive, ref, watch } from 'vue'
import { ArrowLeft, ArrowRight, Loader2, Lock, Minus, Plus } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'

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

const emit = defineEmits(['submit', 'back'])

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

const PH_PHONE_CHARS = /^[0-9+\-\s]+$/
const PH_MOBILE_REGEX = /^(?:09|\+?639)\d{9}$/

function isValidPhMobile(raw) {
  const cleaned = raw.trim()
  if (!cleaned || !PH_PHONE_CHARS.test(cleaned)) return false
  const compact = cleaned.replace(/[\s-]/g, '')
  return PH_MOBILE_REGEX.test(compact)
}

function handleSubmit() {
  localError.value = ''

  if (!props.selectedSlot) {
    localError.value = 'Please select an open slot.'
    return
  }
  if (form.customer_name.trim().length < 2) {
    localError.value = 'Enter your name.'
    return
  }
  if (!isValidPhMobile(form.phone)) {
    localError.value = 'Enter a valid PH mobile number (e.g., 0917 123 4567 or +63 917 123 4567).'
    return
  }
  if (form.address.trim().length < 5) {
    localError.value = 'Enter your home address.'
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
  <section class="space-y-4">
    <!-- Selected Slot Summary Pill + Back -->
    <div class="flex items-center justify-between gap-2">
      <button
        type="button"
        @click="emit('back')"
        class="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm font-semibold text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-950 cursor-pointer"
      >
        <ArrowLeft class="h-4 w-4" />
        <span>Change slot</span>
      </button>

      <span
        v-if="selectedSlot"
        class="rounded-full border border-sky-200/80 bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700"
      >
        {{ selectedSlot.label }}
      </span>
    </div>

    <Card class="p-5 sm:p-6">
      <Transition name="fade-slide">
        <div
          v-if="localError || errorMessage"
          class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm font-medium text-rose-700"
        >
          {{ localError || errorMessage }}
        </div>
      </Transition>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Quantity Stepper -->
        <div class="flex items-center justify-between gap-3 rounded-xl border border-zinc-200/80 bg-zinc-50/70 px-3.5 py-2.5">
          <div>
            <span class="text-sm font-semibold text-zinc-800">Quantity</span>
            <span class="ml-1.5 text-xs text-zinc-400">5-gal container</span>
          </div>

          <div class="inline-flex items-center rounded-lg border border-zinc-200 bg-white p-0.5">
            <button
              type="button"
              @click="adjustQty(-1)"
              :disabled="form.quantity <= 1"
              class="flex h-8 w-8 items-center justify-center rounded-md text-zinc-700 transition hover:bg-zinc-100 active:scale-95 disabled:opacity-35 cursor-pointer"
              aria-label="Decrease"
            >
              <Minus class="h-3.5 w-3.5" />
            </button>
            <span class="min-w-[2.5rem] text-center font-mono text-sm font-bold text-zinc-950">
              {{ form.quantity }}
            </span>
            <button
              type="button"
              @click="adjustQty(1)"
              :disabled="form.quantity >= 20"
              class="flex h-8 w-8 items-center justify-center rounded-md text-zinc-700 transition hover:bg-zinc-100 active:scale-95 disabled:opacity-35 cursor-pointer"
              aria-label="Increase"
            >
              <Plus class="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label for="customer_name" class="mb-1.5 block text-sm font-medium text-zinc-700">Name</label>
            <Input
              id="customer_name"
              v-model="form.customer_name"
              type="text"
              maxlength="100"
              required
              placeholder="Maria Santos"
            />
          </div>

          <div>
            <label for="phone" class="mb-1.5 block text-sm font-medium text-zinc-700">PH Mobile</label>
            <Input
              id="phone"
              v-model="form.phone"
              type="tel"
              inputmode="tel"
              maxlength="16"
              required
              placeholder="0917 123 4567"
            />
          </div>
        </div>

        <div>
          <div class="mb-1.5 flex items-center justify-between">
            <label for="address" class="text-sm font-medium text-zinc-700">Address</label>
            <span class="inline-flex items-center gap-1 text-xs font-medium text-zinc-400">
              <Lock class="h-3 w-3 text-sky-600" />
              Private
            </span>
          </div>
          <Input
            id="address"
            v-model="form.address"
            type="text"
            maxlength="300"
            required
            placeholder="Blk 4 Lot 12 Sampaguita St, Phase 2"
          />
        </div>

        <div>
          <label for="notes" class="mb-1.5 block text-sm font-medium text-zinc-700">
            Note <span class="font-normal text-zinc-400">(optional)</span>
          </label>
          <Input
            id="notes"
            v-model="form.notes"
            type="text"
            maxlength="250"
            placeholder="Green gate, leave by garage"
          />
        </div>

        <div class="pt-2">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            :disabled="submitting || !selectedSlot"
            class="w-full"
          >
            <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
            <span>
              {{ submitting ? 'Placing Order...' : `Place Order (${form.quantity} × 5-gal)` }}
            </span>
            <ArrowRight v-if="!submitting" class="h-4 w-4" />
          </Button>
        </div>
      </form>
    </Card>
  </section>
</template>
