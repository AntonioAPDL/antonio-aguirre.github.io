(function(document) {
  var body = document.body;
  var menuButton = document.querySelector('.sidebar-toggle');
  var sidebar = document.querySelector('#sidebar');
  var themeToggles = document.querySelectorAll('[data-theme-toggle]');
  var root = document.documentElement;
  var lastMenuFocus = null;

  function isMenuOpen() {
    return body.classList.contains('sidebar-open');
  }

  function setMenu(open) {
    body.classList.toggle('sidebar-open', open);
    if (menuButton) {
      menuButton.setAttribute('aria-expanded', open ? 'true' : 'false');
      var label = menuButton.querySelector('.sr-only');
      if (label) label.textContent = open ? 'Close navigation' : 'Open navigation';
    }
  }

  if (menuButton && sidebar) {
    menuButton.addEventListener('click', function() {
      var open = !isMenuOpen();
      if (open) lastMenuFocus = document.activeElement;
      setMenu(open);
    });

    document.addEventListener('click', function(event) {
      if (!isMenuOpen()) return;
      var target = event.target;
      if (sidebar.contains(target) || menuButton.contains(target)) return;
      setMenu(false);
    });

    document.addEventListener('keydown', function(event) {
      if (event.key !== 'Escape' || !isMenuOpen()) return;
      setMenu(false);
      if (lastMenuFocus && typeof lastMenuFocus.focus === 'function') {
        lastMenuFocus.focus();
      } else {
        menuButton.focus();
      }
    });
  }

  function getStoredTheme() {
    try {
      return window.localStorage.getItem('theme');
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      window.localStorage.setItem('theme', theme);
    } catch (e) {}
  }

  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function applyTheme(dark, persist) {
    root.classList.toggle('dark-theme', dark);
    themeToggles.forEach(function(toggle) {
      toggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
      toggle.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
      var icon = toggle.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-moon', !dark);
        icon.classList.toggle('fa-sun', dark);
      }
    });
    if (persist) setStoredTheme(dark ? 'dark' : 'light');
  }

  if (themeToggles.length) {
    var storedTheme = getStoredTheme();
    applyTheme(storedTheme ? storedTheme === 'dark' : systemPrefersDark(), false);
    themeToggles.forEach(function(toggle) {
      toggle.addEventListener('click', function() {
        applyTheme(!root.classList.contains('dark-theme'), true);
      });
    });
  }
})(document);
