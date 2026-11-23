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
  default: 'bg-zinc-950 text-white shadow-xs hover:bg-zinc-800 focus-visible:ring-zinc-950/25',
  primary: 'bg-sky-600 text-white shadow-xs hover:bg-sky-700 focus-visible:ring-sky-500/25',
  secondary: 'bg-zinc-100 text-zinc-900 hover:bg-zinc-200/80 focus-visible:ring-zinc-400/25',
  outline: 'border border-zinc-200 bg-white text-zinc-800 shadow-2xs hover:bg-zinc-50 hover:text-zinc-950 focus-visible:ring-zinc-400/25',
  ghost: 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-950',
}

const sizeClasses = {
  sm: 'h-9 rounded-lg px-3 text-sm',
  default: 'h-10 rounded-xl px-4 text-sm',
  lg: 'h-11 rounded-xl px-5 text-[15px]',
  icon: 'h-9 w-9 rounded-xl',
}

const classes = computed(() =>
  cn(
    'inline-flex items-center justify-center gap-2 font-semibold transition-all duration-150 cursor-pointer select-none active:scale-[0.98] focus-visible:outline-none focus-visible:ring-3 disabled:pointer-events-none disabled:opacity-40',
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
