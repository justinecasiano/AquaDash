<script setup>
import { Check, Clock } from 'lucide-vue-next'
import Badge from '@/components/ui/Badge.vue'
import Progress from '@/components/ui/Progress.vue'

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

function badgeState(slot) {
  if (slot.status === 'CLOSED' || slot.status === 'COMPLETED') {
    return { label: 'Closed', variant: 'secondary', dot: false }
  }
  if (slot.status === 'FULL') {
    return { label: 'Full', variant: 'destructive', dot: false }
  }
  if (slot.remaining <= 3) {
    return { label: 'Few Left', variant: 'warning', dot: true }
  }
  return { label: 'Open', variant: 'success', dot: true }
}

function fillPct(slot) {
  return Math.min(100, Math.round((slot.booked_count / slot.capacity) * 100))
}

function barColor(slot) {
  if (slot.status === 'CLOSED' || slot.status === 'COMPLETED') return 'bg-zinc-300'
  if (slot.status === 'FULL') return 'bg-rose-500'
  if (slot.remaining <= 3) return 'bg-amber-500'
  return 'bg-sky-500'
}
</script>

<template>
  <section class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2.5">
        <span class="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-900 text-xs font-bold text-white">
          1
        </span>
        <h2 class="text-xl font-semibold tracking-tight text-zinc-950">Pick a Delivery Slot</h2>
      </div>
      <Badge variant="secondary">Max 15 / slot</Badge>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !slots.length" class="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="n in 5"
        :key="n"
        class="h-32 animate-pulse rounded-2xl border border-zinc-200/80 bg-white p-5"
      />
    </div>

    <div v-else class="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
      <button
        v-for="(slot, idx) in slots"
        :key="slot.slot_id"
        type="button"
        :disabled="!isSelectable(slot)"
        @click="isSelectable(slot) && emit('select', slot.slot_id)"
        :style="{ animationDelay: `${idx * 45}ms` }"
        class="animate-fade-up group relative flex flex-col justify-between rounded-2xl border p-5 text-left transition-all duration-200"
        :class="[
          selectedSlotId === slot.slot_id && isSelectable(slot)
            ? 'border-sky-600 bg-sky-50/40 shadow-md shadow-sky-500/10 ring-2 ring-sky-500/25'
            : isSelectable(slot)
              ? 'border-zinc-200/90 bg-white shadow-2xs hover:-translate-y-0.5 hover:border-zinc-300 hover:shadow-md cursor-pointer'
              : 'border-zinc-200/70 bg-zinc-100/70 opacity-60 cursor-not-allowed',
        ]"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-2 text-zinc-950">
            <Clock class="h-4 w-4 shrink-0 text-sky-600" />
            <span class="text-lg font-semibold tracking-tight">{{ slot.label }}</span>
          </div>

          <span
            v-if="selectedSlotId === slot.slot_id && isSelectable(slot)"
            class="animate-pop-in flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-600 text-white"
          >
            <Check class="h-3.5 w-3.5 stroke-[3]" />
          </span>
          <Badge v-else :variant="badgeState(slot).variant" :dot="badgeState(slot).dot">
            {{ badgeState(slot).label }}
          </Badge>
        </div>

        <div class="mt-5 space-y-2.5">
          <div class="flex items-baseline justify-between">
            <span
              class="text-base font-bold"
              :class="
                isSelectable(slot)
                  ? slot.remaining <= 3
                    ? 'text-amber-700'
                    : 'text-zinc-950'
                  : 'text-zinc-500'
              "
            >
              <template v-if="isSelectable(slot)">
                {{ slot.remaining }} {{ slot.remaining === 1 ? 'spot' : 'spots' }} left
              </template>
              <template v-else-if="slot.status === 'FULL'">Slot Full</template>
              <template v-else>Ended</template>
            </span>

            <span class="text-sm font-medium text-zinc-500">
              {{ slot.booked_count }}/{{ slot.capacity }}
            </span>
          </div>

          <Progress :value="fillPct(slot)" :bar-class="barColor(slot)" />
        </div>
      </button>
    </div>
  </section>
</template>
