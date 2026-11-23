<script setup>
import { computed } from 'vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'
import Progress from '@/components/ui/Progress.vue'

const props = defineProps({
  selectedDate: {
    type: String,
    required: true,
  },
  slots: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const totals = computed(() => {
  const capacity = props.slots.reduce((sum, s) => sum + s.capacity, 0)
  const booked = props.slots.reduce((sum, s) => sum + s.booked_count, 0)
  const delivered = props.slots.reduce((sum, s) => sum + s.delivered_count, 0)
  const containers = props.slots.reduce((sum, s) => sum + s.total_containers, 0)
  return { capacity, booked, delivered, containers }
})

function fillPct(slot) {
  return Math.min(100, Math.round((slot.booked_count / slot.capacity) * 100))
}

function badgeVariant(status) {
  if (status === 'COMPLETED') return 'success'
  if (status === 'FULL') return 'destructive'
  if (status === 'CLOSED') return 'secondary'
  return 'primary'
}

function barClass(slot) {
  if (slot.status === 'FULL') return 'bg-rose-500'
  if (slot.status === 'COMPLETED') return 'bg-emerald-500'
  if (slot.remaining <= 3 && slot.status === 'OPEN') return 'bg-amber-500'
  return 'bg-sky-600'
}
</script>

<template>
  <section class="space-y-4">
    <!-- Minimalist 3-Metric Strip -->
    <div class="grid grid-cols-3 gap-2.5">
      <Card class="animate-fade-up p-4">
        <span class="text-xs font-medium text-zinc-500">Booked</span>
        <div class="mt-1 flex items-baseline gap-1">
          <span class="text-2xl font-bold tracking-tight text-zinc-950">{{ totals.booked }}</span>
          <span class="font-mono text-xs text-zinc-400">/{{ totals.capacity }}</span>
        </div>
      </Card>

      <Card class="animate-fade-up p-4" style="animation-delay: 40ms">
        <span class="text-xs font-medium text-zinc-500">Jugs</span>
        <div class="mt-1 text-2xl font-bold tracking-tight text-sky-700">{{ totals.containers }}</div>
      </Card>

      <Card class="animate-fade-up p-4" style="animation-delay: 80ms">
        <span class="text-xs font-medium text-zinc-500">Delivered</span>
        <div class="mt-1 flex items-baseline gap-1">
          <span class="text-2xl font-bold tracking-tight text-emerald-600">{{ totals.delivered }}</span>
          <span class="font-mono text-xs text-zinc-400">/{{ totals.booked }}</span>
        </div>
      </Card>
    </div>

    <!-- Clean Slot Bars -->
    <Card class="divide-y divide-zinc-100 overflow-hidden">
      <div
        v-for="(slot, idx) in slots"
        :key="slot.slot_id"
        class="animate-fade-up px-4 py-4 sm:px-5"
        :style="{ animationDelay: `${idx * 40}ms` }"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2.5">
            <span class="text-[15px] font-semibold text-zinc-950">{{ slot.label }}</span>
            <Badge :variant="badgeVariant(slot.status)">{{ slot.status }}</Badge>
          </div>

          <div class="flex items-center gap-3 font-mono text-sm">
            <span class="font-semibold text-zinc-900">{{ slot.booked_count }}/{{ slot.capacity }}</span>
            <span class="text-xs text-zinc-400">{{ slot.total_containers }}j</span>
          </div>
        </div>

        <Progress :value="fillPct(slot)" :bar-class="barClass(slot)" class="mt-2.5 h-1.5" />
      </div>
    </Card>
  </section>
</template>
