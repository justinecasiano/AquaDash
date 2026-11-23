<script setup>
defineProps({
  order: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['new-order'])
</script>

<template>
  <section class="rounded-2xl border border-emerald-200 bg-white p-6 shadow-sm">
    <div class="flex items-start gap-3">
      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-lg font-bold text-emerald-700">
        ✓
      </div>
      <div>
        <h2 class="text-xl font-bold text-slate-900">Order Confirmed!</h2>
        <p class="mt-0.5 text-sm text-slate-600">
          Your 5-gallon water refill delivery is scheduled. Our rider will bring it during your selected time slot.
        </p>
      </div>
    </div>

    <dl class="mt-5 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm sm:grid-cols-2">
      <div>
        <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Order Reference</dt>
        <dd class="mt-0.5 font-mono font-semibold text-slate-900">{{ order.order_id }}</dd>
      </div>
      <div>
        <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Status</dt>
        <dd class="mt-0.5">
          <span class="inline-flex rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
            {{ order.status }}
          </span>
        </dd>
      </div>
      <div>
        <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Delivery Window</dt>
        <dd class="mt-0.5 font-semibold text-slate-900">{{ order.date }} • {{ order.slot_label }}</dd>
      </div>
      <div>
        <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">5-Gallon Containers</dt>
        <dd class="mt-0.5 font-semibold text-slate-900">
          {{ order.quantity }} {{ order.quantity === 1 ? 'container' : 'containers' }}
        </dd>
      </div>
      <div>
        <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Household</dt>
        <dd class="mt-0.5 font-medium text-slate-900">{{ order.customer_name }}</dd>
      </div>
      <div>
        <dt class="text-xs font-medium uppercase tracking-wide text-slate-500">Address Privacy</dt>
        <dd class="mt-0.5 text-slate-600">Stored privately for delivery rider only</dd>
      </div>
    </dl>

    <div class="mt-5">
      <button
        type="button"
        @click="emit('new-order')"
        class="rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-700 cursor-pointer"
      >
        Place Another Order
      </button>
    </div>
  </section>
</template>
