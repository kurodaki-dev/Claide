// Claide website: syntax highlighting, copy buttons, mobile docs menu, TOC highlight.
document.addEventListener("DOMContentLoaded", () => {
  if (window.hljs) document.querySelectorAll("pre code").forEach((el) => window.hljs.highlightElement(el));

  const copy = (text, btn) => {
    navigator.clipboard.writeText(text).then(() => {
      const old = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = old), 1400);
    });
  };

  document.querySelectorAll("[data-copy]").forEach((btn) =>
    btn.addEventListener("click", () => copy(btn.dataset.copy, btn))
  );

  document.querySelectorAll(".doc pre, .split pre").forEach((pre) => {
    const btn = document.createElement("button");
    btn.className = "copy";
    btn.type = "button";
    btn.textContent = "Copy";
    btn.addEventListener("click", () => copy(pre.querySelector("code").innerText, btn));
    pre.appendChild(btn);
  });

  const sidebar = document.querySelector(".sidebar");
  const toggle = document.querySelector(".sidebar-toggle");
  if (sidebar && toggle) {
    toggle.addEventListener("click", () => {
      const open = sidebar.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  const links = [...document.querySelectorAll(".toc a")];
  if (links.length && "IntersectionObserver" in window) {
    const byId = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          links.forEach((a) => a.classList.remove("active"));
          byId.get(e.target.id)?.classList.add("active");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px" });
    document.querySelectorAll(".doc h2[id]").forEach((h) => observer.observe(h));
  }
});
