<template>
  <nav class="menu z-50" aria-label="Primary navigation">
    <div class="container nav-inner">
      <div
        ref="linksRef"
        class="nav-links"
        :class="{ 'nav-links--fade-start': canScrollStart, 'nav-links--fade-end': canScrollEnd }"
        data-testid="nav-links"
        @scroll.passive="updateScrollState"
        @click="revealActiveLink"
      >
        <router-link to="/" class="nav-link"> Dashboard </router-link>
        <router-link to="/accounts" class="nav-link"> Accounts </router-link>
        <router-link to="/transactions" class="nav-link"> Transactions </router-link>
        <router-link to="/forecast" class="nav-link"> Forecast </router-link>
        <router-link to="/planning" class="nav-link"> Planning </router-link>
        <router-link to="/investments" class="nav-link"> Investments </router-link>
      </div>
      <router-link to="/settings" class="nav-link nav-link--secondary" aria-label="Settings">
        <Settings :size="16" aria-hidden="true" />
        <span class="nav-secondary-label">Settings</span>
      </router-link>
      <button
        class="theme-toggle"
        type="button"
        :aria-label="themeToggleLabel"
        :title="themeToggleLabel"
        @click="toggleTheme"
      >
        <Sun v-if="isLightTheme" :size="16" aria-hidden="true" />
        <Moon v-else :size="16" aria-hidden="true" />
        <span>{{ isLightTheme ? 'Light' : 'Dark' }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup>
/**
 * Primary navigation bar with links to top-level routes and a persistent theme toggle.
 */
import { computed, getCurrentInstance, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Moon, Settings, Sun } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'

const { activeTheme, isLightTheme, setTheme } = useTheme()
const themeToggleLabel = computed(() =>
  isLightTheme.value ? 'Switch to Nightfox dark theme' : 'Switch to Everforest light theme',
)

const linksRef = ref(null)
const canScrollStart = ref(false)
const canScrollEnd = ref(false)
const instance = getCurrentInstance()

/** Show an edge fade only on the side(s) where more links are hidden by horizontal scroll. */
function updateScrollState() {
  const el = linksRef.value
  if (!el) return
  const max = el.scrollWidth - el.clientWidth
  canScrollStart.value = el.scrollLeft > 1
  canScrollEnd.value = max > 1 && el.scrollLeft < max - 1
}

/** Keep the current destination visible when the row scrolls (small screens). */
async function revealActiveLink() {
  await nextTick()
  const el = linksRef.value
  const active = el?.querySelector('.router-link-exact-active, [aria-current="page"]')
  active?.scrollIntoView?.({ inline: 'center', block: 'nearest' })
  updateScrollState()
}

onMounted(() => {
  updateScrollState()
  revealActiveLink()
  window.addEventListener('resize', updateScrollState)
})
onBeforeUnmount(() => window.removeEventListener('resize', updateScrollState))
watch(() => instance?.proxy?.$route?.fullPath, revealActiveLink)

/** Toggle between the two supported application themes. */
function toggleTheme() {
  setTheme(activeTheme.value === 'everforest-light' ? 'nightfox' : 'everforest-light')
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.nav-link.router-link-exact-active {
  background-color: var(--hover-bg);
  color: var(--color-text-light);
  font-weight: 600;
  box-shadow: inset 0 -2px 0 var(--accent-primary);
}

.nav-link--secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  flex: 0 0 auto;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.menu {
  background-color: var(--background);
  border-bottom: 1px solid var(--divider);
  box-shadow: 0 2px 4px var(--shadow);
  position: sticky;
  top: 0;
  backdrop-filter: blur(6px);
}

.nav-inner,
.nav-links {
  display: flex;
  align-items: center;
}

.nav-inner {
  justify-content: center;
  gap: 1rem;
  padding: 0.5rem 0;
}

.nav-links {
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.nav-link {
  color: var(--color-text-light);
  font-size: 0.95rem;
  font-weight: 500;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  transition:
    color 0.3s ease,
    background-color 0.25s ease,
    box-shadow 0.25s ease;
  text-decoration: none;
  cursor: pointer;
}

.nav-link:hover {
  color: var(--link-hover-color);
  background-color: var(--hover-bg);
  box-shadow: inset 0 -2px 0 var(--link-hover-color);
}

.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  flex: 0 0 auto;
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2);
  background: var(--surface-2);
  color: var(--text-secondary);
  font: inherit;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s ease;
}

.theme-toggle:hover,
.theme-toggle:focus-visible {
  border-color: var(--accent-primary);
  color: var(--accent-primary-strong);
  background: var(--accent-surface);
  outline: none;
  box-shadow: 0 0 0 2px var(--interactive-focus);
}

/* Avoid wrapping six primary destinations at intermediate widths. */
@media (max-width: 1100px) {
  .nav-inner {
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    min-width: 0;
    padding-inline: 0.5rem;
  }

  .nav-links {
    justify-content: flex-start;
    overflow-x: auto;
    flex-wrap: nowrap;
    min-width: 0;
    flex: 1 1 auto;
    scrollbar-width: none;
    scroll-padding-inline: 1.5rem;
    scroll-snap-type: x proximity;
  }

  .nav-links::-webkit-scrollbar {
    display: none;
  }

  /* Edge fades cue that more destinations are off-screen in that direction. */
  .nav-links--fade-end {
    mask-image: linear-gradient(to right, #000 calc(100% - 1.75rem), transparent);
  }

  .nav-links--fade-start {
    mask-image: linear-gradient(to right, transparent, #000 1.75rem);
  }

  .nav-links--fade-start.nav-links--fade-end {
    mask-image: linear-gradient(
      to right,
      transparent,
      #000 1.75rem,
      #000 calc(100% - 1.75rem),
      transparent
    );
  }

  .nav-link {
    flex: 0 0 auto;
    white-space: nowrap;
    scroll-snap-align: center;
    font-size: 0.875rem;
    padding: 0.45rem 0.65rem;
  }

  .nav-secondary-label,
  .theme-toggle span {
    display: none;
  }
}
</style>
