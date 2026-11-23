<script setup>
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  variant: {
    type: String,
    default: 'secondary',
  },
  dot: {
    type: Boolean,
    default: false,
  },
  class: {
    type: String,
    default: '',
  },
})

const variants = {
  default: 'bg-zinc-900 text-white border-transparent',
  primary: 'bg-sky-50 text-sky-700 border-sky-200/80',
  secondary: 'bg-zinc-100 text-zinc-700 border-zinc-200/70',
  success: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
  warning: 'bg-amber-50 text-amber-700 border-amber-200/80',
  destructive: 'bg-rose-50 text-rose-700 border-rose-200/80',
}

const dotColors = {
  default: 'bg-white',
  primary: 'bg-sky-500',
  secondary: 'bg-zinc-400',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  destructive: 'bg-rose-500',
}

const classes = computed(() =>
  cn(
    'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold tracking-wide',
    variants[props.variant] || variants.secondary,
    props.class,
  ),
)
</script>

<template>
  <span :class="classes">
    <span
      v-if="dot"
      class="h-1.5 w-1.5 rounded-full"
      :class="[dotColors[variant] || dotColors.secondary, variant === 'success' ? 'animate-pulse' : '']"
    />
    <slot />
  </span>
</template>
