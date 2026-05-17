<script setup>
defineProps({
  views: {
    type: Array,
    required: true
  },
  modelValue: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="view-switcher">
    <button
      v-for="view in views"
      :key="view.key"
      class="switch-btn"
      :class="{ active: modelValue === view.key }"
      @click="emit('update:modelValue', view.key)"
    >
      <svg v-if="view.icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="switch-icon" v-html="view.icon" />
      {{ view.label }}
    </button>
  </div>
</template>

<style scoped>
.view-switcher {
  display: flex;
  gap: 2px;
  background: var(--color-neutral-100);
  border-radius: 8px;
  padding: 3px;
}

.switch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-neutral-500);
  transition: all 0.2s;
  white-space: nowrap;
}

.switch-btn:hover {
  color: var(--color-neutral-700);
}

.switch-btn.active {
  background: white;
  color: var(--color-primary-600);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.switch-icon {
  width: 15px;
  height: 15px;
}
</style>