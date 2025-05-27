<template>
  <div class="gallery-container">
    <h1>Charts Gallery - 600px by 400px Standard - More Specs Here</h1>
    </div>

    <!-- Example of a 2-column layout; each chart is in its own container -->
    <div class="charts-grid">
      <!-- Daily Net Chart -->
      <div class="chart-item">
        <h2>Daily Net Income</h2>
        <DailyNetIncomeChart />
      </div>

      <!-- Category Spend Chart -->
      <div class="chart-item">
        <h2>Spend by Category</h2>
        <CategoryBreakdownChart />
      </div>

      <div class="chart-item">
        <h2>Assets Bar Trended</h2>
        <AssetsBarTrended />
      </div>
      

      <div class="chart-item">
        <h2>Assets Year Comparison</h2>
        <AssetsYearComparisonChart />
      </div>

      <div class="chart-item">
        <h2>Net Year Comparison</h2>
        <NetYearComparisonChart />
      </div>

      <div class="chart-item">
        <h2>Liabilities Year Comparison</h2>
        <LiabilitiesYearComparisonChart />
      </div>

    </div>
    <footer class="dashboard-footer">
      &copy; good dashroad.
    </footer>
  
</template>

<script>
import DailyNetIncomeChart from "../components/DailyNetIncomeChart.vue";
import AssetsYearComparisonChart from "../components/AssetsYearComparisonChart.vue";
import NetYearComparisonChart from "../components/NetYearComparisonChart.vue";
import LiabilitiesYearComparisonChart from "@/components/LiabilitiesYearComparisonChart.vue";
import AssetsBarTrended from "@/components/charts/AssetsBarTrended.vue";
import CategoryBreakdownChart from "@/components/charts/CategoryBreakdownChart.vue";

export default {
  name: "Dashboard",
  components: {
    DailyNetIncomeChart,
    CategoryBreakdownChart,
    AssetsYearComparisonChart,
    NetYearComparisonChart,
    LiabilitiesYearComparisonChart,
    AssetsBarTrended
  },
  
  };
</script>
<style scoped>
.gallery-container {
  padding: 1rem;
  font-family: "Fira Code", monospace;
  color: #ebdbb2;
  background-color: #282828;
  max-height: 100px;
}

h1 {
  margin-bottom: 1.5rem;
  color: #fabd2f; /* Gruvbox yellow accent */
}

h2 {
  gap: 1rem;
}

/* The grid that holds our chart items */
.charts-grid {
  display: flex;
  flex-wrap: wrap;      /* allow items to wrap if space is limited */
  row-gap: 5rem;
  column-gap: 1.5rem;
  margin-bottom: auto;
}

/* Each chart container item */
.chart-item {
  flex: 1 1 45%;        /* 2 columns in a row, each ~ 45% of width, gap:1rem leaves ~10% leftover */
  background-color: #3c3836;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
  padding-inline: 1.5rem;
  padding-bottom: 6rem;
  padding-top: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.chart-item h2 {
  margin: 0 0 0 0;
  color: #fabd2f; /* accent color for headings */
}


</style >