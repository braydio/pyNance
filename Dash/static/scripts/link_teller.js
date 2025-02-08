document.addEventListener("DOMContentLoaded", function () {
  // Fetch the link token from the backend
  fetch("/generate_link_token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        const linkToken = data.link_token;

        // Initialize Teller Connect with the link token
        var tellerConnect = TellerConnect.setup({
          linkToken: linkToken,
          products: ["transactions", "balance"],
          onInit: function () {
            console.log("Teller Connect has initialized");
          },
          onSuccess: function (enrollment) {
            // Log the enrollment details
            console.log("User enrolled successfully", enrollment);

            // Send the token to your backend
            fetch("/save_token", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                access_token: enrollment.accessToken, // Send the token
                user_id: enrollment.user.id, // Optionally send the user ID
              }),
            })
              .then((response) => response.json())
              .then((data) => {
                if (data.status === "success") {
                  console.log("Token saved successfully");
                } else {
                  console.error("Error saving token:", data.error);
                }
              })
              .catch((error) => {
                console.error("Error:", error);
              });
          },
          onExit: function () {
            console.log("User closed Teller Connect");
          },
        });

        // Attach Teller Connect to the button
        var el = document.getElementById("teller-connect");
        el.addEventListener("click", function () {
          tellerConnect.open();
        });
      } else {
        console.error("Failed to fetch link token:", data.message);
      }
    })
    .catch((error) => {
      console.error("Error fetching link token:", error);
    });
});
