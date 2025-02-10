document.addEventListener("DOMContentLoaded", function () {
  var tellerConnect = TellerConnect.setup({
    applicationId: "app_p9ohmuos5p7om9h4k8000", // Replace with your app ID
    products: ["transactions", "balance"], // Specify the products you need
    onInit: function () {
      console.log("Teller Connect initialized");
    },
    onSuccess: function (enrollment) {
      console.log("Enrollment successful", enrollment);

      // Send token and user ID to backend
      fetch("http://127.0.0.1:5000/save_token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          access_token: enrollment.accessToken,
          user_id: enrollment.user.id,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "success") {
            console.log("Token saved successfully");
          } else {
            console.error("Error saving token:", data.message);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
        });
    },
    onExit: function () {
      console.log("User exited Teller Connect");
    },
  });

  document.getElementById("teller-connect").addEventListener("click", function () {
    tellerConnect.open();
  });
});

fetch("/get_all_accounts", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
  },
})
  .then((response) => response.json())
  .then((data) => {
    if (data.status === "success") {
      const accounts = data.data;
      const tableBody = document.querySelector("#linked-accounts tbody");

      // Clear existing rows
      tableBody.innerHTML = "";

      // Add rows for each account
      accounts.forEach((account) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${account.institution?.name || "Unknown"}</td>
          <td>${account.name}</td>
          <td>${account.balances?.available || "N/A"}</td>
        `;
        tableBody.appendChild(row);
      });
    } else {
      console.error("Error fetching accounts:", data.message);
    }
  })
  .catch((error) => {
    console.error("Error:", error);
  });
fetch("/get_all_accounts", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
  },
})
  .then((response) => response.json())
  .then((data) => {
    if (data.status === "success") {
      const accounts = data.data;
      const tableBody = document.querySelector("#linked-accounts tbody");

      // Clear existing rows
      tableBody.innerHTML = "";

      // Add rows for each account
      accounts.forEach((account) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${account.institution?.name || "Unknown"}</td>
          <td>${account.name}</td>
          <td>${account.balances?.available || "N/A"}</td>
        `;
        tableBody.appendChild(row);
      });
    } else {
      console.error("Error fetching accounts:", data.message);
    }
  })
  .catch((error) => {
    console.error("Error:", error);
  });


  