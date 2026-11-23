<script setup>
import { computed } from 'vue'

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

function statusPill(status) {
  switch (status) {
    case 'COMPLETED':
      return 'bg-emerald-100 text-emerald-800'
    case 'FULL':
      return 'bg-rose-100 text-rose-700'
    case 'CLOSED':
      return 'bg-slate-200 text-slate-700'
    default:
      return 'bg-sky-100 text-sky-800'
  }
}

function barClass(slot) {
  if (slot.status === 'FULL') return 'bg-rose-500'
  if (slot.status === 'COMPLETED') return 'bg-emerald-500'
  if (slot.remaining <= 3 && slot.status === 'OPEN') return 'bg-amber-500'
  return 'bg-sky-600'
}
</script>

<template>
  <section class="space-y-5">
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">Owner Slot Capacity Monitor</h2>
          <p class="text-sm text-slate-500">
            Live slot fullness for <span class="font-medium text-slate-700">{{ selectedDate }}</span> (aggregate counts only — zero private home addresses).
          </p>
        </div>
        <span v-if="loading" class="text-xs font-medium text-sky-600">Refreshing...</span>
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Slots Booked</p>
          <p class="mt-1 text-2xl font-bold text-slate-900">
            {{ totals.booked }} <span class="text-sm font-normal text-slate-500">/ {{ totals.capacity }}</span>
          </p>
          <p class="mt-0.5 text-xs text-slate-500">{{ totals.pct }}% of daily capacity</p>
        </div>

        <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">5-Gallon Jugs</p>
          <p class="mt-1 text-2xl font-bold text-sky-700">{{ totals.containers }}</p>
          <p class="mt-0.5 text-xs text-slate-500">Total containers to prepare</p>
        </div>

        <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Pending Deliveries</p>
          <p class="mt-1 text-2xl font-bold text-amber-600">{{ totals.pending }}</p>
          <p class="mt-0.5 text-xs text-slate-500">Awaiting rider completion</p>
        </div>

        <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">Delivered</p>
          <p class="mt-1 text-2xl font-bold text-emerald-600">{{ totals.delivered }}</p>
          <p class="mt-0.5 text-xs text-slate-500">Completed orders</p>
        </div>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 class="mb-4 text-base font-semibold text-slate-900">Capacity Breakdown by Time Slot</h3>

      <div class="space-y-4">
        <div
          v-for="slot in slots"
          :key="slot.slot_id"
          class="rounded-xl border border-slate-200 p-4"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2.5">
              <span class="font-semibold text-slate-900">{{ slot.label }}</span>
              <span
                class="rounded-full px-2.5 py-0.5 text-xs font-semibold"
                :class="statusPill(slot.status)"
              >
                {{ slot.status }}
              </span>
            </div>

            <div class="flex flex-wrap items-center gap-4 text-xs text-slate-600">
              <span>
                <strong class="text-slate-900">{{ slot.booked_count }} / {{ slot.capacity }}</strong> orders ({{ fillPct(slot) }}%)
              </span>
              <span>
                <strong class="text-slate-900">{{ slot.total_containers }}</strong> jugs
              </span>
              <span>
                Pending: <strong class="text-amber-700">{{ slot.pending_count }}</strong> •
                Delivered: <strong class="text-emerald-700">{{ slot.delivered_count }}</strong>
              </span>
            </div>
          </div>

          <div class="mt-3 h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="barClass(slot)"
              :style="{ width: `${fillPct(slot)}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
