(function(document) {
  var toggle = document.querySelector('.sidebar-toggle');
  var sidebar = document.querySelector('#sidebar');
  var checkbox = document.querySelector('#sidebar-checkbox');

  if (!toggle || !sidebar || !checkbox) return;

  document.addEventListener('click', function(e) {
    var target = e.target;

    if (!checkbox.checked ||
       sidebar.contains(target) ||
       (target === checkbox || target === toggle)) return;

    checkbox.checked = false;
  }, false);
})(document);

document.addEventListener('DOMContentLoaded', function() {
  var toggles = document.querySelectorAll('[data-theme-toggle]');
  var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  var storedTheme = window.localStorage.getItem('theme');
  var isDark = storedTheme ? storedTheme === 'dark' : prefersDark;

  function applyTheme(dark, persist) {
    document.body.classList.toggle('dark-theme', dark);
    toggles.forEach(function(toggle) {
      toggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
      var icon = toggle.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-moon', !dark);
        icon.classList.toggle('fa-sun', dark);
      }
    });
    if (persist) {
      window.localStorage.setItem('theme', dark ? 'dark' : 'light');
    }
  }

  if (toggles.length) {
    applyTheme(isDark, false);
    toggles.forEach(function(toggle) {
      toggle.addEventListener('click', function() {
        applyTheme(!document.body.classList.contains('dark-theme'), true);
      });
    });
  }
});
