<script setup>
import { Check, Droplets, Lock, RotateCcw } from 'lucide-vue-next'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'

defineProps({
  order: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['new-order'])
</script>

<template>
  <Card class="animate-fade-up mx-auto max-w-xl p-7 sm:p-9 text-center">
    <div
      class="animate-pop-in mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
    >
      <Check class="h-8 w-8 stroke-[2.75]" />
    </div>

    <h2 class="mt-5 text-2xl font-bold tracking-tight text-zinc-950">Order Confirmed</h2>
    <p class="mt-1.5 text-base text-zinc-500">
      Scheduled for <strong class="text-zinc-900">{{ order.slot_label }}</strong> ({{ order.date }})
    </p>

    <div class="mt-7 grid grid-cols-2 gap-3 text-left">
      <div class="rounded-xl border border-zinc-200/80 bg-zinc-50 p-4">
        <span class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Reference</span>
        <p class="mt-1 truncate font-mono text-base font-bold text-zinc-950">{{ order.order_id }}</p>
      </div>

      <div class="rounded-xl border border-zinc-200/80 bg-zinc-50 p-4">
        <span class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Quantity</span>
        <p class="mt-1 flex items-center gap-1.5 text-base font-bold text-sky-700">
          <Droplets class="h-4 w-4" />
          {{ order.quantity }} {{ order.quantity === 1 ? 'Jug' : 'Jugs' }}
        </p>
      </div>

      <div class="rounded-xl border border-zinc-200/80 bg-zinc-50 p-4">
        <span class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Household</span>
        <p class="mt-1 truncate text-base font-semibold text-zinc-950">{{ order.customer_name }}</p>
      </div>

      <div class="rounded-xl border border-zinc-200/80 bg-zinc-50 p-4">
        <span class="text-xs font-semibold uppercase tracking-wider text-zinc-500">Status</span>
        <div class="mt-1">
          <Badge variant="warning" dot>{{ order.status }}</Badge>
        </div>
      </div>
    </div>

    <div class="mt-5 inline-flex items-center gap-1.5 text-sm text-zinc-500">
      <Lock class="h-4 w-4 text-sky-600" />
      <span>Address kept private for delivery rider only</span>
    </div>

    <div class="mt-7">
      <Button variant="default" size="lg" class="w-full sm:w-auto" @click="emit('new-order')">
        <RotateCcw class="h-4 w-4" />
        <span>Place Another Order</span>
      </Button>
    </div>
  </Card>
</template>
