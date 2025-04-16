
<template>
  <div>
    <button @click="downloadCSV" class="btn btn-primary">
      Download Accounts CSV
    </button>
  </div>
</template>

<script>
export default {
  name: "DownloadAccountsCSV",
  methods: {
    async downloadCSV() {
      try {
        const response = await fetch("/export/accounts");

        if (!response.ok) {
          throw new Error("Failed to fetch CSV");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.setAttribute("download", "accounts_export.csv");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error("Download error:", err);
        alert("Failed to download CSV.");
      }
    },
  },
};
</script>
