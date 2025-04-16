
<template>
  <div class="space-y-2">
    <button @click="downloadCSV" class="btn btn-primary">Download Accounts CSV</button>

    <input type="file" @change="uploadCSV" accept=".csv" />
  </div>
</template>

<script>
export default {
  name: "AccountCSVTools",
  methods: {
    async downloadCSV() {
      const response = await fetch("/tools/export/accounts");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = "accounts_export.csv";
      link.click();
      link.remove();
    },

    async uploadCSV(event) {
      const file = event.target.files[0];
      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("/tools/upload/accounts", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();
        alert(data.status || "Upload complete.");
      } catch (err) {
        alert("Upload failed.");
        console.error(err);
      }
    },
  },
};
</script>
