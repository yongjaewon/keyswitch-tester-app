<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSystemStore } from '../stores/system'

const router = useRouter()
const store = useSystemStore()

const pin = ref('')
const error = ref('')

async function verifyPin() {
  try {
    const response = await fetch(`http://localhost:8000/auth?pin=${pin.value}`, {
      method: 'POST'
    });
    
    if (response.ok) {
      store.setPin(pin.value)
      router.push('/dashboard')
    } else {
      error.value = 'Invalid PIN'
      pin.value = ''
    }
  } catch (err) {
    error.value = 'Connection error'
    console.error(err)
  }
}
</script>

<template>
  <div class="pin-entry">
    <div class="pin-container">
      <h2>Enter PIN</h2>
      <div class="pin-input">
        <input 
          type="password" 
          v-model="pin" 
          maxlength="4" 
          placeholder="****"
          @keyup.enter="verifyPin"
        >
      </div>
      <button @click="verifyPin" :disabled="pin.length !== 4">
        Enter
      </button>
      <p class="error" v-if="error">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.pin-entry {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f5f5;
}

.pin-container {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

h2 {
  margin-bottom: 1.5rem;
  color: #333;
}

input {
  font-size: 1.5rem;
  width: 120px;
  padding: 0.5rem;
  text-align: center;
  margin-bottom: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

input:focus {
  outline: none;
  border-color: #007bff;
}

button {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

button:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background: #0056b3;
}

.error {
  color: #dc3545;
  margin-top: 1rem;
  margin-bottom: 0;
}
</style> 