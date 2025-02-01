document.addEventListener("DOMContentLoaded", () => {
    const institutionsContainer = document.getElementById("institutions-container");
  
    async function refreshItem(itemId, product) {
      try {
        const response = await fetch("/refresh_item", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ item_id: itemId, product: product }),
        });
  
        const data = await response.json();
        if (data.status === "success") {
          alert(`${product} successfully refreshed for ${itemId}`);
        } else {
          alert(`Error: ${data.error}`);
        }
      } catch (error) {
        console.error("Error refreshing item:", error);
        alert("Failed to refresh item. Check console for details.");
      }
    }
  
    function createRefreshButton(itemId, product) {
      const button = document.createElement("button");
      button.textContent = `Refresh ${product}`;
      button.onclick = () => refreshItem(itemId, product);
      return button;
    }
  
    async function fetchAndRenderInstitutions() {
      try {
        const response = await fetch("/get_institutions");
        const data = await response.json();
  
        if (data.status === "success") {
          institutionsContainer.innerHTML = "";
  
          Object.entries(data.institutions).forEach(([institutionName, institution]) => {
            const institutionDiv = document.createElement("div");
            institutionDiv.classList.add("institution");
  
            const title = document.createElement("h3");
            title.textContent = institutionName;
            institutionDiv.appendChild(title);
  
            institution.products.forEach((product) => {
              const button = createRefreshButton(institution.item_id, product);
              institutionDiv.appendChild(button);
            });
  
            institutionsContainer.appendChild(institutionDiv);
          });
        }
      } catch (error) {
        console.error("Error fetching institutions:", error);
      }
    }
  
    fetchAndRenderInstitutions();
  });
  