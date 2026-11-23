<script setup>
defineProps({
  slots: {
    type: Array,
    required: true,
  },
  selectedSlotId: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select'])

function isSelectable(slot) {
  return slot.status === 'OPEN'
}

function badgeMeta(slot) {
  if (slot.status === 'CLOSED' || slot.status === 'COMPLETED') {
    return { text: 'Closed', classes: 'bg-slate-200 text-slate-600' }
  }
  if (slot.status === 'FULL') {
    return { text: 'Full (15/15)', classes: 'bg-rose-100 text-rose-700' }
  }
  if (slot.remaining <= 3) {
    return { text: `Almost Full`, classes: 'bg-amber-100 text-amber-800' }
  }
  return { text: 'Open', classes: 'bg-emerald-100 text-emerald-700' }
}

function fillPercent(slot) {
  return Math.min(100, Math.round((slot.booked_count / slot.capacity) * 100))
}

function barColor(slot) {
  if (slot.status === 'CLOSED' || slot.status === 'COMPLETED') return 'bg-slate-400'
  if (slot.status === 'FULL') return 'bg-rose-500'
  if (slot.remaining <= 3) return 'bg-amber-500'
  return 'bg-sky-500'
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex items-center justify-between gap-2">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">1. Choose a Delivery Time Slot</h2>
        <p class="text-sm text-slate-500">Each time slot accepts up to 15 household orders.</p>
      </div>
      <span v-if="loading" class="text-xs font-medium text-sky-600">Updating...</span>
    </div>

    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <button
        v-for="slot in slots"
        :key="slot.slot_id"
        type="button"
        :disabled="!isSelectable(slot)"
        @click="isSelectable(slot) && emit('select', slot.slot_id)"
        class="group relative flex flex-col rounded-xl border p-4 text-left transition"
        :class="[
          selectedSlotId === slot.slot_id && isSelectable(slot)
            ? 'border-sky-600 bg-sky-50/70 ring-2 ring-sky-500/30'
            : isSelectable(slot)
              ? 'border-slate-200 bg-white hover:border-sky-400 hover:bg-slate-50/70 cursor-pointer'
              : 'border-slate-200 bg-slate-50/80 opacity-65 cursor-not-allowed',
        ]"
      >
        <div class="flex items-start justify-between gap-2">
          <span class="font-semibold text-slate-900">{{ slot.label }}</span>
          <span
            class="inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
            :class="badgeMeta(slot).classes"
          >
            {{ badgeMeta(slot).text }}
          </span>
        </div>

        <div class="mt-3 flex items-baseline justify-between text-xs text-slate-600">
          <span>{{ slot.booked_count }} / {{ slot.capacity }} booked</span>
          <span v-if="isSelectable(slot)" class="font-medium text-sky-700">
            {{ slot.remaining }} {{ slot.remaining === 1 ? 'spot' : 'spots' }} left
          </span>
          <span v-else-if="slot.status === 'FULL'" class="font-medium text-rose-600">
            No spots left
          </span>
          <span v-else class="font-medium text-slate-500">
            Booking ended
          </span>
        </div>

        <div class="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full transition-all duration-300"
            :class="barColor(slot)"
            :style="{ width: `${fillPercent(slot)}%` }"
          ></div>
        </div>
      </button>
    </div>
  </section>
</template>
