(function () {
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || form.id !== "tribe-bar-form") return;

    event.preventDefault();
    var dateInput = form.querySelector('[name="tribe-bar-date"]');
    var date = dateInput ? dateInput.value.trim() : "";
    var parts = window.location.pathname.split("/");
    var eventsIdx = parts.indexOf("events");
    var base =
      eventsIdx === -1
        ? "."
        : parts.slice(0, eventsIdx + 1).join("/") + "/";

    if (/^\d{4}-\d{2}$/.test(date)) {
      window.location.href = base + date + "/index.html";
      return;
    }
    window.location.href = base + "index.html";
  });
})();
