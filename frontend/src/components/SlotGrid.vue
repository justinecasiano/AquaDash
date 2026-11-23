<script setup>
import { ArrowRight, Check } from 'lucide-vue-next'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
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

const emit = defineEmits(['select', 'next'])

function isSelectable(slot) {
  return slot.status === 'OPEN'
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
    <!-- Loading skeleton -->
    <div v-if="loading && !slots.length" class="space-y-2.5">
      <div
        v-for="n in 5"
        :key="n"
        class="h-20 animate-pulse rounded-2xl border border-zinc-200/80 bg-white"
      />
    </div>

    <div v-else class="space-y-2.5">
      <button
        v-for="(slot, idx) in slots"
        :key="slot.slot_id"
        type="button"
        :disabled="!isSelectable(slot)"
        @click="isSelectable(slot) && emit('select', slot.slot_id)"
        :style="{ animationDelay: `${idx * 40}ms` }"
        class="animate-fade-up group flex w-full items-center justify-between gap-4 rounded-2xl border px-4 py-4 text-left transition-all duration-150 sm:px-5"
        :class="[
          selectedSlotId === slot.slot_id && isSelectable(slot)
            ? 'border-sky-600 bg-sky-50/40 shadow-sm ring-2 ring-sky-500/20'
            : isSelectable(slot)
              ? 'border-zinc-200/90 bg-white shadow-2xs hover:border-zinc-300 hover:shadow-sm cursor-pointer'
              : 'border-zinc-200/60 bg-zinc-100/60 opacity-55 cursor-not-allowed',
        ]"
      >
        <div class="min-w-0 flex-1 space-y-2">
          <div class="flex items-center justify-between gap-2">
            <span class="text-[16px] font-semibold tracking-tight text-zinc-950">
              {{ slot.label }}
            </span>

            <span
              v-if="isSelectable(slot)"
              class="text-sm font-semibold"
              :class="slot.remaining <= 3 ? 'text-amber-600' : 'text-zinc-600'"
            >
              {{ slot.remaining }} left
            </span>
            <Badge v-else-if="slot.status === 'FULL'" variant="destructive">Full</Badge>
            <Badge v-else variant="secondary">Closed</Badge>
          </div>

          <Progress :value="fillPct(slot)" :bar-class="barColor(slot)" class="h-1.5" />
        </div>

        <div
          class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition-all duration-150"
          :class="
            selectedSlotId === slot.slot_id && isSelectable(slot)
              ? 'animate-pop-in border-sky-600 bg-sky-600 text-white'
              : 'border-zinc-300 bg-white group-hover:border-zinc-400'
          "
        >
          <Check v-if="selectedSlotId === slot.slot_id && isSelectable(slot)" class="h-3.5 w-3.5 stroke-[3]" />
        </div>
      </button>
    </div>

    <div class="pt-2">
      <Button
        variant="default"
        size="lg"
        class="w-full"
        :disabled="!selectedSlotId"
        @click="emit('next')"
      >
        <span>Continue</span>
        <ArrowRight class="h-4 w-4" />
      </Button>
    </div>
  </section>
</template>
