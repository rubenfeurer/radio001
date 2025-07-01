<template>
  <div class="signal-strength" :class="sizeClass">
    <div
      v-for="bar in 4"
      :key="bar"
      class="signal-bar"
      :class="{
        'signal-active': bar <= activeBars,
        'signal-inactive': bar > activeBars
      }"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  strength: number
  size?: 'xs' | 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md'
})

// Calculate number of active bars based on signal strength
const activeBars = computed(() => {
  if (props.strength >= 75) return 4
  if (props.strength >= 50) return 3
  if (props.strength >= 25) return 2
  if (props.strength > 0) return 1
  return 0
})

// Size classes
const sizeClass = computed(() => {
  switch (props.size) {
    case 'xs': return 'signal-xs'
    case 'sm': return 'signal-sm'
    case 'md': return 'signal-md'
    case 'lg': return 'signal-lg'
    default: return 'signal-md'
  }
})

// Signal strength color
const signalColor = computed(() => {
  if (props.strength >= 75) return 'text-green-500'
  if (props.strength >= 50) return 'text-yellow-500'
  if (props.strength >= 25) return 'text-orange-500'
  return 'text-red-500'
})
</script>

<style scoped>
.signal-strength {
  @apply flex items-end space-x-0.5;
}

.signal-bar {
  @apply bg-current rounded-sm transition-colors duration-200;
}

/* Size variants */
.signal-xs .signal-bar {
  @apply w-0.5;
}

.signal-xs .signal-bar:nth-child(1) { @apply h-1; }
.signal-xs .signal-bar:nth-child(2) { @apply h-1.5; }
.signal-xs .signal-bar:nth-child(3) { @apply h-2; }
.signal-xs .signal-bar:nth-child(4) { @apply h-2.5; }

.signal-sm .signal-bar {
  @apply w-0.5;
}

.signal-sm .signal-bar:nth-child(1) { @apply h-1; }
.signal-sm .signal-bar:nth-child(2) { @apply h-2; }
.signal-sm .signal-bar:nth-child(3) { @apply h-3; }
.signal-sm .signal-bar:nth-child(4) { @apply h-4; }

.signal-md .signal-bar {
  @apply w-1;
}

.signal-md .signal-bar:nth-child(1) { @apply h-1.5; }
.signal-md .signal-bar:nth-child(2) { @apply h-2.5; }
.signal-md .signal-bar:nth-child(3) { @apply h-3.5; }
.signal-md .signal-bar:nth-child(4) { @apply h-4; }

.signal-lg .signal-bar {
  @apply w-1;
}

.signal-lg .signal-bar:nth-child(1) { @apply h-2; }
.signal-lg .signal-bar:nth-child(2) { @apply h-3; }
.signal-lg .signal-bar:nth-child(3) { @apply h-4; }
.signal-lg .signal-bar:nth-child(4) { @apply h-5; }

/* Signal strength colors */
.signal-active {
  @apply text-green-500;
}

.signal-inactive {
  @apply text-gray-300 dark:text-gray-600;
}

/* Signal strength based coloring */
.signal-strength:has(.signal-bar:nth-child(4).signal-active) .signal-active {
  @apply text-green-500;
}

.signal-strength:has(.signal-bar:nth-child(3).signal-active):not(:has(.signal-bar:nth-child(4).signal-active)) .signal-active {
  @apply text-yellow-500;
}

.signal-strength:has(.signal-bar:nth-child(2).signal-active):not(:has(.signal-bar:nth-child(3).signal-active)) .signal-active {
  @apply text-orange-500;
}

.signal-strength:has(.signal-bar:nth-child(1).signal-active):not(:has(.signal-bar:nth-child(2).signal-active)) .signal-active {
  @apply text-red-500;
}
</style>
