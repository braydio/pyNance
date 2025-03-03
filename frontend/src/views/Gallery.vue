<template>
  <div class="gallery-container">
    <h1>Charts Gallery - Testing for Visuals and Pink Floyd</h1>
    </div>

    <!-- Example of a 2-column layout; each chart is in its own container -->
    <div class="charts-grid">
      <div class="chart-item">
        <h2>Pink Floyd</h2>
        <div class="video-container">
          <iframe
            width="560"
            height="315"
            src="https://www.youtube.com/embed/o7VO6_beRRE?si=fbgY_g-JIcSigZq7"
            title="YouTube video player"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
          </iframe>
        </div>
      </div>

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
        <h2>Net Year Comparison</h2>
        <NetYearComparisonChart />
      </div>
    </div>

    <footer class="dashboard-footer">
      &copy; good dashroad.
    </footer>
  
</template>

<script>
import DailyNetIncomeChart from "../components/DailyNetChart.vue";
import NetYearComparisonChart from "../components/NetYearComparisonChart.vue";
import AssetsBarTrended from "@/components/AssetsBarTrended.vue";
import CategoryBreakdownChart from "@/components/CategoryBreakdownChart.vue";

export default {
  name: "Dashboard",
  components: {
    DailyNetIncomeChart,
    CategoryBreakdownChart,
    NetYearComparisonChart,
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
  row-gap: 1rem;
  column-gap: 1rem;
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
  height: 400px;
  width: 600px;
}
/* Optional: Style the video container for responsiveness */
.video-container {
  position: relative;
  padding-bottom: 56.25%; /* 16:9 ratio */
  padding-top: 25px;
  height: 400px;
  width: 100%;
}
.video-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 500px;
  height: 400px;
}

.chart-item h2 {
  margin: 0 0 0 0;
  color: #fabd2f; /* accent color for headings */
}


</style >