(() => {
  const pages = [
    ["Route participants and duration", "dashboard1.html"],
    ["Transaction type and continuity", "dashboard_2.html"],
    ["Path continuity and duration", "dashboard_3.html"],
    ["Business vs Consumer payments", "try4.html"],
    ["Party text patterns", "dashboard5.html"],
    ["Currency and FX mix", "dashboard6/dashboard6_version2.html"],
    ["FX steps and duration", "dashboard7/dashboard7_slide(final).html"],
    ["Anomaly labels", "dashboard_8.html"],
    ["Anomaly-label rate by currency", "dashboard_9.html"],
    ["Anomaly-label rates by hour and type", "daahboard_10.html"],
    ["Transaction timing", "dashboard11/dashboard11.html"],
  ];

  const current = Number(document.body.dataset.dashboard);
  const root = document.body.dataset.dashboardRoot || ".";
  const page = pages[current - 1];
  if (!page) return;

  const link = (label, href, className) => {
    const element = document.createElement("a");
    element.textContent = label;
    element.href = `${root}/${href}`;
    if (className) element.className = className;
    return element;
  };

  const nav = document.createElement("nav");
  nav.className = "dashboard-nav";
  nav.setAttribute("aria-label", "Dashboard navigation");
  nav.append(link("Dashboard hub", "index.html", "nav-home"));

  const previous = current > 1
    ? link("← Previous", pages[current - 2][1])
    : link("← Previous", "#");
  if (current === 1) {
    previous.classList.add("nav-disabled");
    previous.setAttribute("aria-disabled", "true");
  }
  nav.append(previous);

  const position = document.createElement("span");
  position.className = "nav-current";
  position.textContent = document.body.dataset.dashboardLabel || `Dashboard ${current} of ${pages.length}`;
  nav.append(position);

  const select = document.createElement("select");
  select.setAttribute("aria-label", "Jump to dashboard");
  const isArchivedCopy = Boolean(document.body.dataset.dashboardLabel);
  if (isArchivedCopy) {
    const option = document.createElement("option");
    option.value = page[1];
    option.textContent = `Open current Dashboard ${current}`;
    option.selected = true;
    select.append(option);
  }
  pages.forEach(([title, href], index) => {
    const option = document.createElement("option");
    option.value = href;
    option.textContent = `Dashboard ${index + 1} — ${title}`;
    option.selected = !isArchivedCopy && index + 1 === current;
    select.append(option);
  });
  select.addEventListener("change", () => {
    window.location.href = `${root}/${select.value}`;
  });
  nav.append(select);

  const next = current < pages.length
    ? link("Next →", pages[current][1])
    : link("Next →", "#");
  if (current === pages.length) {
    next.classList.add("nav-disabled");
    next.setAttribute("aria-disabled", "true");
  }
  nav.append(next);

  const exportButton = document.createElement("button");
  exportButton.type = "button";
  exportButton.className = "nav-export";
  exportButton.textContent = "Convert to PDF";
  exportButton.title = "Save this dashboard as a PDF";
  exportButton.addEventListener("click", () => window.print());
  nav.append(exportButton);

  document.body.prepend(nav);
})();
