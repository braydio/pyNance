document.addEventListener("DOMContentLoaded", () => {
    const themeSelect = document.getElementById("theme-select");
    const themeForm = document.getElementById("theme-form");
    const themeStatus = document.getElementById("theme-status");

    // Fetch available themes and the current theme
    fetch("/themes")
        .then(response => response.json())
        .then(data => {
            if (data.themes) {
                const themes = data.themes;
                const currentTheme = data.current_theme;

                // Populate the dropdown with themes
                themes.forEach(theme => {
                    const option = document.createElement("option");
                    option.value = theme;
                    option.textContent = theme;

                    // Preselect the current theme
                    if (theme === currentTheme) {
                        option.selected = true;
                    }

                    themeSelect.appendChild(option);
                });

                themeStatus.textContent = `Current theme: ${currentTheme}`;
            } else {
                themeStatus.textContent = data.error || "No themes available.";
            }
        })
        .catch(err => {
            console.error("Error fetching themes:", err);
            themeStatus.textContent = "Error loading themes.";
        });

    // Handle form submission
    themeForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const selectedTheme = themeSelect.value;

        fetch("/set_theme", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ theme: selectedTheme }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    themeStatus.textContent = `Theme applied: ${data.theme}`;
                    // Update the theme dynamically without reloading
                    document.querySelector("link[rel='stylesheet']").href =
                        `/static/themes/${data.theme}`;
                } else {
                    themeStatus.textContent = `Error: ${data.error}`;
                }
            })
            .catch(err => {
                console.error("Error setting theme:", err);
                themeStatus.textContent = "Error applying theme.";
            });
    });
});
