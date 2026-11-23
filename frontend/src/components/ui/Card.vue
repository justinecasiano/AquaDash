<script setup>
import { cn } from '@/lib/utils'

defineProps({
  class: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <div
    :class="
      cn(
        'rounded-2xl border border-zinc-200/80 bg-white text-zinc-950 shadow-xs transition-shadow duration-200',
        $props.class,
      )
    "
  >
    <slot />
  </div>
</template>
