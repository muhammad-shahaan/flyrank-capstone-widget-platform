(function () {
    // Find the script that loaded this widget
    const script = document.currentScript;

    if (!script) {
        console.error("Widget script could not be detected.");
        return;
    }

    // Read widget ID from:
    // data-widget-id="1"
    const widgetId = script.getAttribute("data-widget-id");

    if (!widgetId) {
        console.error("Missing data-widget-id.");
        return;
    }

    // Backend URL is automatically taken from script src
    const scriptUrl = new URL(script.src);
    const apiBase = scriptUrl.origin;

    async function loadWidget() {
        try {
            // -----------------------------------------
            // Fetch Public Widget Configuration
            // -----------------------------------------

            const response = await fetch(
                `${apiBase}/widgets/${widgetId}/config`
            );

            if (!response.ok) {
                throw new Error(
                    `Widget config failed: ${response.status}`
                );
            }

            const data = await response.json();
            const widget = data.widget;

            // -----------------------------------------
            // Create Widget Container
            // -----------------------------------------

            const container = document.createElement("div");

            container.style.maxWidth = "420px";
            container.style.padding = "20px";
            container.style.margin = "20px 0";
            container.style.border = "1px solid #ddd";
            container.style.borderRadius = "10px";
            container.style.fontFamily = "Arial, sans-serif";
            container.style.background = "#ffffff";

            // -----------------------------------------
            // Widget Title
            // -----------------------------------------

            const title = document.createElement("h2");
            title.textContent = widget.title;

            // -----------------------------------------
            // Description
            // -----------------------------------------

            const description = document.createElement("p");
            description.textContent = widget.description;

            // -----------------------------------------
            // Form
            // -----------------------------------------

            const form = document.createElement("form");

            // Name
            const nameInput = document.createElement("input");
            nameInput.type = "text";
            nameInput.placeholder = "Your name";
            nameInput.required = true;
            nameInput.maxLength = 100;

            // Email
            const emailInput = document.createElement("input");
            emailInput.type = "email";
            emailInput.placeholder = "Your email";
            emailInput.required = true;
            emailInput.maxLength = 254;

            // Message
            const messageInput = document.createElement("textarea");
            messageInput.placeholder = "Your message";
            messageInput.required = true;
            messageInput.maxLength = 1000;

            // -----------------------------------------
            // Honeypot
            // -----------------------------------------

            const websiteInput = document.createElement("input");

            websiteInput.type = "text";
            websiteInput.name = "website";
            websiteInput.tabIndex = -1;
            websiteInput.autocomplete = "off";

            // Hide honeypot from normal users
            websiteInput.style.position = "absolute";
            websiteInput.style.left = "-9999px";

            // -----------------------------------------
            // Submit Button
            // -----------------------------------------

            const button = document.createElement("button");

            button.type = "submit";
            button.textContent = widget.button_text;

            // -----------------------------------------
            // Result Message
            // -----------------------------------------

            const result = document.createElement("p");

            // -----------------------------------------
            // Basic Styling
            // -----------------------------------------

            const fields = [
                nameInput,
                emailInput,
                messageInput
            ];

            fields.forEach((field) => {
                field.style.display = "block";
                field.style.width = "100%";
                field.style.boxSizing = "border-box";
                field.style.padding = "10px";
                field.style.marginBottom = "10px";
            });

            messageInput.rows = 4;

            button.style.padding = "10px 16px";
            button.style.cursor = "pointer";

            // -----------------------------------------
            // Add Elements
            // -----------------------------------------

            form.appendChild(nameInput);
            form.appendChild(emailInput);
            form.appendChild(messageInput);
            form.appendChild(websiteInput);
            form.appendChild(button);
            form.appendChild(result);

            container.appendChild(title);
            container.appendChild(description);
            container.appendChild(form);

            // Put widget immediately after embed script
            script.insertAdjacentElement(
                "afterend",
                container
            );

            // -----------------------------------------
            // Submit Lead
            // -----------------------------------------

            form.addEventListener(
                "submit",
                async function (event) {
                    event.preventDefault();

                    button.disabled = true;
                    result.textContent = "Sending...";

                    const submission = {
                        widget_id: Number(widgetId),
                        name: nameInput.value,
                        email: emailInput.value,
                        message: messageInput.value,
                        website: websiteInput.value
                    };

                    try {
                        const submitResponse = await fetch(
                            `${apiBase}/submissions`,
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type": "application/json"
                                },

                                body: JSON.stringify(submission)
                            }
                        );

                        const submitData =
                            await submitResponse.json();

                        if (!submitResponse.ok) {
                            throw new Error(
                                submitData.detail ||
                                submitData.error ||
                                "Submission failed"
                            );
                        }

                        result.textContent =
                            "Thank you! Your message was submitted.";

                        form.reset();

                    } catch (error) {

                        console.error(error);

                        result.textContent =
                            "Unable to submit. Please try again.";

                    } finally {

                        button.disabled = false;
                    }
                }
            );

        } catch (error) {

            console.error(
                "Widget failed to load:",
                error
            );
        }
    }

    loadWidget();
})();