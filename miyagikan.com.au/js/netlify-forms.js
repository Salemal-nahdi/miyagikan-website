(function () {
  function encodeForm(form) {
    return new URLSearchParams(new FormData(form)).toString();
  }

  function showMessage(container, text, isError) {
    if (!container) return;
    container.textContent = text;
    container.className = "w-form-message type_" + (isError ? "error" : "success");
    container.style.display = "block";
  }

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || !form.hasAttribute("data-netlify")) return;

    event.preventDefault();
    event.stopPropagation();

    var messageEl = form.querySelector(".w-form-message");
    var submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    fetch("/", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: encodeForm(form),
    })
      .then(function (response) {
        if (!response.ok) throw new Error("Submission failed");
        form.reset();
        showMessage(
          messageEl,
          form.getAttribute("data-success-message") ||
            "Thank you! Your message was sent.",
          false
        );
        if (form.getAttribute("data-redirect")) {
          window.location.href = form.getAttribute("data-redirect");
        }
      })
      .catch(function () {
        showMessage(
          messageEl,
          "Sorry, something went wrong. Please try again or call us directly.",
          true
        );
      })
      .finally(function () {
        if (submitBtn) submitBtn.disabled = false;
      });
  }, true);
})();
