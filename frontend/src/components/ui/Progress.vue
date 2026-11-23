<script setup>
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  value: {
    type: Number,
    default: 0,
  },
  barClass: {
    type: String,
    default: 'bg-sky-600',
  },
  class: {
    type: String,
    default: '',
  },
})

const clamped = computed(() => Math.min(100, Math.max(0, props.value)))
</script>

<template>
  <div :class="cn('h-2 w-full overflow-hidden rounded-full bg-zinc-100', $props.class)">
    <div
      class="h-full rounded-full transition-all duration-500 ease-out"
      :class="barClass"
      :style="{ width: `${clamped}%` }"
    />
  </div>
</template>
