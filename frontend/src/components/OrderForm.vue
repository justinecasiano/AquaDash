<script setup>
import { reactive, ref, watch } from 'vue'
import { ArrowRight, Loader2, Lock, Minus, Plus } from 'lucide-vue-next'
import Badge from '@/components/ui/Badge.vue'
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

const emit = defineEmits(['submit'])

const quickQuantities = [1, 2, 3, 5]

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

function handleSubmit() {
  localError.value = ''

  if (!props.selectedSlot) {
    localError.value = 'Select an open time slot above first.'
    return
  }
  if (form.customer_name.trim().length < 2) {
    localError.value = 'Enter your name (at least 2 characters).'
    return
  }
  if (form.address.trim().length < 5) {
    localError.value = 'Enter your subdivision address (Block, Lot, Street).'
    return
  }
  if (form.phone.trim().length < 7) {
    localError.value = 'Enter a valid contact number.'
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
  <section class="animate-fade-up space-y-4" style="animation-delay: 120ms">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-2.5">
        <span class="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-900 text-xs font-bold text-white">
          2
        </span>
        <h2 class="text-xl font-semibold tracking-tight text-zinc-950">Your Details</h2>
      </div>

      <Badge v-if="selectedSlot" variant="primary">
        {{ selectedDate }} · {{ selectedSlot.label }}
      </Badge>
    </div>

    <Card class="p-6 sm:p-7">
      <Transition name="fade-slide">
        <div
          v-if="localError || errorMessage"
          class="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-base font-medium text-rose-700"
        >
          {{ localError || errorMessage }}
        </div>
      </Transition>

      <form @submit.prevent="handleSubmit" class="space-y-5">
        <!-- 5-Gallon Quantity Picker -->
        <div>
          <label class="mb-2 block text-base font-medium text-zinc-800">5-Gallon Jugs</label>
          <div class="flex flex-wrap items-center gap-3">
            <div class="inline-flex items-center rounded-xl border border-zinc-200 bg-zinc-50/60 p-1">
              <button
                type="button"
                @click="adjustQty(-1)"
                :disabled="form.quantity <= 1"
                class="flex h-10 w-10 items-center justify-center rounded-lg text-zinc-700 transition hover:bg-white hover:shadow-2xs active:scale-95 disabled:opacity-35 cursor-pointer"
                aria-label="Decrease quantity"
              >
                <Minus class="h-4 w-4" />
              </button>
              <span class="min-w-[3.5rem] text-center text-xl font-bold text-zinc-950">
                {{ form.quantity }}
              </span>
              <button
                type="button"
                @click="adjustQty(1)"
                :disabled="form.quantity >= 20"
                class="flex h-10 w-10 items-center justify-center rounded-lg text-zinc-700 transition hover:bg-white hover:shadow-2xs active:scale-95 disabled:opacity-35 cursor-pointer"
                aria-label="Increase quantity"
              >
                <Plus class="h-4 w-4" />
              </button>
            </div>

            <div class="flex items-center gap-2">
              <button
                v-for="q in quickQuantities"
                :key="q"
                type="button"
                @click="form.quantity = q"
                class="h-10 min-w-[2.75rem] rounded-xl border px-3 text-sm font-semibold transition active:scale-95 cursor-pointer"
                :class="
                  form.quantity === q
                    ? 'border-sky-600 bg-sky-50 text-sky-700'
                    : 'border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-950'
                "
              >
                {{ q }}
              </button>
            </div>
          </div>
        </div>

        <div class="grid gap-5 sm:grid-cols-2">
          <div>
            <label for="customer_name" class="mb-2 block text-base font-medium text-zinc-800">
              Name
            </label>
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
            <label for="phone" class="mb-2 block text-base font-medium text-zinc-800">
              Mobile Number
            </label>
            <Input
              id="phone"
              v-model="form.phone"
              type="tel"
              maxlength="20"
              required
              placeholder="0917 123 4567"
            />
          </div>
        </div>

        <div>
          <div class="mb-2 flex items-center justify-between gap-2">
            <label for="address" class="text-base font-medium text-zinc-800">Home Address</label>
            <span class="inline-flex items-center gap-1 text-xs font-medium text-zinc-500">
              <Lock class="h-3.5 w-3.5 text-sky-600" />
              Private · Rider only
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
          <label for="notes" class="mb-2 block text-base font-medium text-zinc-800">
            Delivery Note <span class="font-normal text-zinc-400">(optional)</span>
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
            <Loader2 v-if="submitting" class="h-5 w-5 animate-spin" />
            <span>
              {{
                submitting
                  ? 'Placing Order...'
                  : `Order ${form.quantity} ${form.quantity === 1 ? 'Jug' : 'Jugs'}`
              }}
            </span>
            <ArrowRight v-if="!submitting" class="h-5 w-5" />
          </Button>
        </div>
      </form>
    </Card>
  </section>
</template>
