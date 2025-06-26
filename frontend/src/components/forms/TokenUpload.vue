<template>
  <div class="link-account">
    <h2>Okay Genius Go Ahead</h2>

    <transition name="fade">
      <div class="upload-form-inline" v-if="showForm">
        <label class="text-xs font-medium" for="userId">User ID</label>
        <input id="userId" v-model="userId" class="input-text" placeholder="Well?" />

        <label class="text-xs font-medium" for="accessToken">Access Token</label>
        <textarea id="accessToken" v-model="accessToken" class="input-textarea" rows="2"
          placeholder="You said you knew what you were doing."></textarea>

        <button @click="submit" :disabled="!userId || !accessToken || loading" class="forms-btn">
          Upload
        </button>
        <button class="forms-btn" @click="$emit('cancel')">Cancel</button>
      </div>
    </transition>

    <p v-if="successMessage" class="success-badge">
      {{ successMessage }}
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const showForm = ref(true)
const userId = ref('')
const accessToken = ref('')
const loading = ref(false)
const successMessage = ref('')

const submit = async () => {
  loading.value = true
  try {
    const response = await axios.post('/api/upload/accounts', {
      user_id: userId.value,
      access_token: accessToken.value,
    })

    const { provider, account_count, institution_name } = response.data
    alert(`✔️ Uploaded ${account_count} ${provider} account(s) from ${institution_name}`)

    showForm.value = false
    userId.value = ''
    accessToken.value = ''
  } catch (e) {
    alert(e.response?.data?.error || e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.link-account {
  margin: 0 auto;
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border-top: 8px inset var(--color-bg-secondary);
  border-bottom: 8px inset var(--color-text-muted);
  border-left: 6px outset var(--color-bg-secondary);
  border-right: 6px outset var(--color-text-muted);
  border-radius: 5px;
  text-align: center;
}

.link-account h2 {
  margin: 5px 1px;
  color: var(--neon-purple);
}

.upload-form-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--divider);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.input-text,
.input-textarea {
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 0.5rem;
  font-family: var(--font-mono);
}

.input-text {
  width: 160px;
}

.input-textarea {
  width: 300px;
}

.forms-btn {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
  padding: 0.5rem 1.25rem;
}

.forms-btn:hover {
  color: var(--themed-bg);
  background-color: var(--neon-mint);
}

.success-badge {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-bg-success, #2ecc71);
  color: #fff;
  border-radius: 6px;
  font-weight: bold;
}
</style>


<style scoped>
@reference "../../assets/css/main.css";
.link-account {
  margin: 0 auto;
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border-top: 8px inset var(--color-bg-secondary);
  border-bottom: 6px inset var(--color-text-muted);
  border-left: 8px outset var(--color-bg-secondary);
  border-right: 6px outset var(--color-text-muted);
  border-radius: 5px;
  text-align: center;
}

.link-account h2 {
  margin: 5px 1px;
  color: var(--neon-purple);
}

.upload-form-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--divider);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.input-text,
.input-textarea {
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 0.5rem;
  font-family: var(--font-mono);
}

.input-text {
  width: 160px;
}

.input-textarea {
  width: 300px;
}

.forms-btn {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
  padding: 0.5rem 1.25rem;
}

.forms-btn:hover {
  color: var(--themed-bg);
  background-color: var(--neon-mint);
}

.success-badge {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-bg-success, #2ecc71);
  color: #fff;
  border-radius: 6px;
  font-weight: bold;
}
</style>
