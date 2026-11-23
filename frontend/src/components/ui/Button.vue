<script setup>
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  variant: {
    type: String,
    default: 'default',
  },
  size: {
    type: String,
    default: 'default',
  },
  type: {
    type: String,
    default: 'button',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  class: {
    type: String,
    default: '',
  },
})

const variantClasses = {
  default: 'bg-zinc-950 text-white shadow-xs hover:bg-zinc-800 focus-visible:ring-zinc-950/30',
  primary: 'bg-sky-600 text-white shadow-xs hover:bg-sky-700 focus-visible:ring-sky-500/30',
  secondary: 'bg-zinc-100 text-zinc-900 hover:bg-zinc-200/80 focus-visible:ring-zinc-400/30',
  outline: 'border border-zinc-200 bg-white text-zinc-900 shadow-2xs hover:bg-zinc-50 focus-visible:ring-zinc-400/30',
  ghost: 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950',
}

const sizeClasses = {
  sm: 'h-9 rounded-lg px-3.5 text-sm',
  default: 'h-11 rounded-xl px-5 text-base',
  lg: 'h-12 rounded-xl px-6 text-base',
  icon: 'h-10 w-10 rounded-xl',
}

const classes = computed(() =>
  cn(
    'inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 cursor-pointer select-none active:scale-[0.98] focus-visible:outline-none focus-visible:ring-3 disabled:pointer-events-none disabled:opacity-45',
    variantClasses[props.variant] || variantClasses.default,
    sizeClasses[props.size] || sizeClasses.default,
    props.class,
  ),
)
</script>

<template>
  <button :type="type" :disabled="disabled" :class="classes">
    <slot />
  </button>
</template>
