(function () {
  var PAGES = [
    { url: "/miyagikan.com.au/index-p-1083.html", title: "Home" },
    { url: "/miyagikan.com.au/about/index-p-1083.html", title: "About" },
    { url: "/miyagikan.com.au/classes/index-p-1083.html", title: "Classes" },
    { url: "/miyagikan.com.au/instructors/index-p-1083.html", title: "Instructors" },
    { url: "/miyagikan.com.au/locations/index-p-1083.html", title: "Locations" },
    { url: "/miyagikan.com.au/gallery/index-p-1083.html", title: "Gallery" },
    { url: "/miyagikan.com.au/events/index-ical-1.html", title: "Events" },
    { url: "/miyagikan.com.au/links/index-p-1083.html", title: "Links" },
    { url: "/miyagikan.com.au/enquiry/index-p-1083.html", title: "Contact" },
    { url: "/miyagikan.com.au/blog/index-p-1083.html", title: "Blog" },
  ];

  function relativePrefix() {
    var depth = (window.location.pathname.match(/\//g) || []).length;
    var rootDepth = window.location.pathname.indexOf("/miyagikan.com.au/") === 0 ? 2 : 0;
    var up = Math.max(0, depth - rootDepth - 1);
    return up ? "../".repeat(up) : "./";
  }

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || !form.classList.contains("site-search-form")) return;
    event.preventDefault();

    var query = (form.querySelector('[name="s"]') || {}).value || "";
    query = query.trim().toLowerCase();
    if (!query) return;

    var prefix = relativePrefix();
    var target = prefix + "search/index-p-1083.html?q=" + encodeURIComponent(query);
    window.location.href = target;
  });
})();
