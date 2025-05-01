<template>
  <div class="forecast-container">
    <h2>30-Day Forecasted Delta</h2>

    <div class="summary">
      <p><strong>Current Balance:</strong> ${{ currentBalance.toFixed(2) }}</p>
      <p><strong>Forecasted Delta:</strong> <span :class="{ gain: forecastDelta >= 0, loss: forecastDelta < 0 }">
        ${{ forecastDelta.toFixed(2) }}</span>
      </p>
      <p><strong>Projected Balance:</strong> ${{ (currentBalance + forecastDelta).toFixed(2) }}</p>
    </div>

    <div class="inputs">
      <label>Manual Recurring Income ($):</label>
      <input type="number" v-model.number="manualIncome" @input="recalculateForecast" />

      <label>Monthly Liabilities Rate (%):</label>
      <input type="number" v-model.number="liabilityRate" @input="recalculateForecast" />
    </div>

    <h3>Forecast Drivers</h3>
    <ul>
      <li>+ Salary (expected): $2500</li>
      <li>- Rent: $1200</li>
      <li>- Subscriptions: $200</li>
      <li>+ Investments Return: $300</li>
      <li>- Liability Deductions: ${{ liabilityImpact.toFixed(2) }}</li>
      <li>+ Manual Recurring: ${{ manualIncome.toFixed(2) }}</li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'Forecast',
  data() {
    return {
      currentBalance: 4300,
      manualIncome: 0,
      liabilityRate: 2.1, // percent
      forecastDelta: 0,
      liabilityImpact: 0,
    };
  },
  mounted() {
    this.recalculateForecast();
  },
  methods: {
    recalculateForecast() {
      const salary = 2500;
      const rent = -1200;
      const subscriptions = -200;
      const investmentReturn = 300;
      const liabilityImpact = -(this.currentBalance * this.liabilityRate / 100);

      const net = salary + rent + subscriptions + investmentReturn + this.manualIncome + liabilityImpact;

      this.forecastDelta = net;
      this.liabilityImpact = liabilityImpact;
    },
  },
};
</script>

<style scoped>
.forecast-container {
  max-width: 600px;
  margin: auto;
  padding: 1rem;
  font-family: sans-serif;
}

.summary {
  margin-bottom: 1rem;
}

.gain {
  color: green;
}

.loss {
  color: red;
}

.inputs label {
  display: block;
  margin-top: 1em;
}

input[type="number"] {
  width: 100%;
  padding: 0.5em;
  margin-bottom: 1em;
}
</style>