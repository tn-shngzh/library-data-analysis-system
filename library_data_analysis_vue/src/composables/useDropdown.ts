import { ref, onMounted, onUnmounted } from 'vue'

export const useDropdown = () => {
  const showDropdown = ref(false)
  const dropdownRef = ref(null)

  const toggleDropdown = () => {
    showDropdown.value = !showDropdown.value
  }

  const closeDropdown = (event) => {
    if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
      showDropdown.value = false
    }
  }

  onMounted(() => {
    document.addEventListener('click', closeDropdown)
  })

  onUnmounted(() => {
    document.removeEventListener('click', closeDropdown)
  })

  return { showDropdown, dropdownRef, toggleDropdown, closeDropdown }
}
