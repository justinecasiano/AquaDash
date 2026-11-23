<script setup>
import { cn } from '@/lib/utils'

defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  class: {
    type: String,
    default: '',
  },
})

defineEmits(['update:modelValue'])
</script>

<template>
  <input
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
    v-bind="$attrs"
    :class="
      cn(
        'flex h-11 w-full rounded-xl border border-zinc-200 bg-white px-3.5 text-[15px] text-zinc-950 shadow-2xs transition-all duration-150 placeholder:text-zinc-400 hover:border-zinc-300 focus:border-sky-500 focus:ring-3 focus:ring-sky-500/15 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50',
        $props.class,
      )
    "
  />
</template>
