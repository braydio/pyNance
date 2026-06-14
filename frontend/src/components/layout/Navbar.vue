<template>
  <nav
    class="menu z-50"
    aria-label="Primary navigation"
  >
    <div class="container nav-inner">
      <div class="nav-links">
        <router-link
          to="/"
          class="nav-link"
        >
          Dashboard
        </router-link>
        <router-link
          to="/accounts"
          class="nav-link"
        >
          Accounts
        </router-link>
        <router-link
          to="/transactions"
          class="nav-link"
        >
          Transactions
        </router-link>
        <router-link
          to="/forecast"
          class="nav-link"
        >
          Forecasting
        </router-link>
        <router-link
          to="/planning"
          class="nav-link"
        >
          Planning
        </router-link>
        <router-link
          to="/investments"
          class="nav-link"
        >
          Investments
        </router-link>
      </div>
      <button
        class="theme-toggle"
        type="button"
        :aria-label="themeToggleLabel"
        :title="themeToggleLabel"
        @click="toggleTheme"
      >
        <Sun
          v-if="isLightTheme"
          :size="16"
          aria-hidden="true"
        />
        <Moon
          v-else
          :size="16"
          aria-hidden="true"
        />
        <span>{{ isLightTheme ? 'Light' : 'Dark' }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup>
/**
 * Primary navigation bar with links to top-level routes and a persistent theme toggle.
 */
import { computed } from 'vue'
import { Moon, Sun } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'

const { activeTheme, isLightTheme, setTheme } = useTheme()
const themeToggleLabel = computed(() =>
  isLightTheme.value ? 'Switch to Nightfox dark theme' : 'Switch to Everforest light theme',
)

/** Toggle between the two supported application themes. */
function toggleTheme() {
  setTheme(activeTheme.value === 'everforest-light' ? 'nightfox' : 'everforest-light')
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.nav-link.router-link-exact-active {
  background-color: var(--hover-bg);
  color: var(--accent-primary);
  font-weight: bold;
  box-shadow: inset 0 -2px 0 var(--accent-primary);
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
  font-size: 0.8rem;
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

@media (max-width: 760px) {
  .nav-inner {
    align-items: flex-start;
  }

  .nav-links {
    justify-content: flex-start;
    overflow-x: auto;
    flex-wrap: nowrap;
  }

  .theme-toggle span {
    display: none;
  }
}
</style>
