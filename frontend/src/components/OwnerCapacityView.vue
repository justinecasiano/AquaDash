<script setup>
import { computed } from 'vue'
import { CheckCircle2, Droplets, Package } from 'lucide-vue-next'
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
  const pending = props.slots.reduce((sum, s) => sum + s.pending_count, 0)
  const containers = props.slots.reduce((sum, s) => sum + s.total_containers, 0)
  const pct = capacity > 0 ? Math.round((booked / capacity) * 100) : 0
  return { capacity, booked, delivered, pending, containers, pct }
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
  <section class="space-y-6">
    <!-- Top 3 Big Stat Cards -->
    <div class="grid gap-4 sm:grid-cols-3">
      <Card class="animate-fade-up p-5">
        <div class="flex items-center justify-between text-zinc-500">
          <span class="text-sm font-medium">Booked Today</span>
          <Package class="h-5 w-5 text-zinc-400" />
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-bold tracking-tight text-zinc-950">{{ totals.booked }}</span>
          <span class="text-base font-medium text-zinc-400">/ {{ totals.capacity }}</span>
          <span class="ml-auto text-sm font-semibold text-sky-700">{{ totals.pct }}%</span>
        </div>
      </Card>

      <Card class="animate-fade-up p-5" style="animation-delay: 50ms">
        <div class="flex items-center justify-between text-zinc-500">
          <span class="text-sm font-medium">5-Gallon Jugs</span>
          <Droplets class="h-5 w-5 text-sky-500" />
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-bold tracking-tight text-sky-700">{{ totals.containers }}</span>
          <span class="text-sm font-medium text-zinc-400">containers</span>
        </div>
      </Card>

      <Card class="animate-fade-up p-5" style="animation-delay: 100ms">
        <div class="flex items-center justify-between text-zinc-500">
          <span class="text-sm font-medium">Delivered</span>
          <CheckCircle2 class="h-5 w-5 text-emerald-500" />
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-bold tracking-tight text-emerald-600">{{ totals.delivered }}</span>
          <span class="text-base font-medium text-zinc-400">/ {{ totals.booked }}</span>
          <span v-if="totals.pending > 0" class="ml-auto text-sm font-medium text-amber-600">
            {{ totals.pending }} pending
          </span>
        </div>
      </Card>
    </div>

    <!-- Clean Slot Capacity List -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold tracking-tight text-zinc-950">Slots · {{ selectedDate }}</h2>
        <span class="text-sm text-zinc-500">Counts only · No addresses</span>
      </div>

      <div class="space-y-3">
        <Card
          v-for="(slot, idx) in slots"
          :key="slot.slot_id"
          class="animate-fade-up p-5"
          :style="{ animationDelay: `${idx * 45}ms` }"
        >
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <span class="text-lg font-semibold text-zinc-950">{{ slot.label }}</span>
              <Badge :variant="badgeVariant(slot.status)" :dot="slot.status === 'OPEN'">
                {{ slot.status }}
              </Badge>
            </div>

            <div class="flex items-center gap-4 text-base">
              <span class="font-bold text-zinc-950">
                {{ slot.booked_count }} <span class="font-normal text-zinc-400">/ {{ slot.capacity }}</span>
              </span>
              <span class="text-sm font-medium text-zinc-500">{{ slot.total_containers }} jugs</span>
              <span class="text-sm font-semibold text-emerald-600">{{ slot.delivered_count }} done</span>
            </div>
          </div>

          <Progress :value="fillPct(slot)" :bar-class="barClass(slot)" class="mt-3.5 h-2.5" />
        </Card>
      </div>
    </div>
  </section>
</template>
