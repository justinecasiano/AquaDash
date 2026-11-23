<script setup>
import { Check, RotateCcw } from 'lucide-vue-next'
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
  <Card class="animate-fade-up p-7 text-center sm:p-8">
    <div
      class="animate-pop-in mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"
    >
      <Check class="h-7 w-7 stroke-[2.75]" />
    </div>

    <h2 class="mt-4 text-2xl font-bold tracking-tight text-zinc-950">Order Confirmed</h2>
    <p class="mt-1 text-sm font-medium text-zinc-500">
      {{ order.slot_label }} · {{ order.date }}
    </p>

    <div class="mt-6 grid grid-cols-3 gap-2.5 text-left">
      <div class="rounded-xl border border-zinc-200/80 bg-zinc-50 p-3">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Ref</span>
        <p class="mt-0.5 truncate font-mono text-sm font-semibold text-zinc-900">{{ order.order_id }}</p>
      </div>

      <div class="rounded-xl border border-zinc-200/80 bg-zinc-50 p-3">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Jugs</span>
        <p class="mt-0.5 text-sm font-bold text-sky-700">{{ order.quantity }} × 5-gal</p>
      </div>

      <div class="rounded-xl border border-zinc-200/80 bg-zinc-50 p-3">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Name</span>
        <p class="mt-0.5 truncate text-sm font-semibold text-zinc-900">{{ order.customer_name }}</p>
      </div>
    </div>

    <div class="mt-6">
      <Button variant="default" size="lg" class="w-full" @click="emit('new-order')">
        <RotateCcw class="h-4 w-4" />
        <span>New Order</span>
      </Button>
    </div>
  </Card>
</template>
