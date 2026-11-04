
document.addEventListener("DOMContentLoaded", async () => {
  const nav = document.querySelector("header nav");

  if (!nav) return;

  // Avoid adding the link twice.
  if (nav.querySelector(".wq-account-link")) return;

  const accountLink = document.createElement("a");
  accountLink.className = "wq-account-link";
  accountLink.href = "/login";
  accountLink.textContent = "Sign In";

  nav.appendChild(accountLink);

  try {
    const response = await fetch("/api/me", {
      credentials: "same-origin",
      cache: "no-store"
    });

    if (!response.ok) return;

    const user = await response.json();

    if (user.authenticated === true) {
      accountLink.href = "/account";
      accountLink.textContent = "My Account";
    }
  } catch (error) {
    // Keep the Sign In link available if the status check fails.
    console.warn("Account status unavailable.");
  }
});
