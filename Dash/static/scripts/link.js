    // Fetch the link token from the Flask backend
    fetch('/get_link_token')
      .then(response => response.json())
      .then(data => {
        if (data.link_token) {
          const handler = Plaid.create({
            token: data.link_token,
            onSuccess: function(public_token, metadata) {
              alert("Public Token: " + public_token);
              console.log("Public Token:", public_token);

              // Save the public token and automatically get the access token
              fetch('/save_public_token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ public_token: public_token })
              }).then(response => response.json())
                .then(data => {
                  if (data.access_token) {
                    console.log("Access Token:", data.access_token);
                    document.getElementById("status").textContent = "Access token received: " + data.access_token;
                  } else {
                    console.error("Error:", data.error);
                    document.getElementById("status").textContent = "Failed to get access token.";
                  }
                });

            },
            onExit: function(err, metadata) {
              if (err) {
                console.error("Error during exit:", err);
                document.getElementById("status").textContent = "User exited with an error.";
              } else {
                console.log("User exited without error.");
                document.getElementById("status").textContent = "User exited without error.";
              }
            }
          });

          document.getElementById("link-button").onclick = function() {
            handler.open();
          };

        } else {
          alert("Error fetching link token: " + data.error);
        }
      })
      .catch(error => {
        console.error("Error fetching link token:", error);
      });