(function(document) {
  var toggle = document.querySelector('.sidebar-toggle');
  var sidebar = document.querySelector('#sidebar');
  var checkbox = document.querySelector('#sidebar-checkbox');

  document.addEventListener('click', function(e) {
    var target = e.target;

    if(!checkbox.checked ||
       sidebar.contains(target) ||
       (target === checkbox || target === toggle)) return;

    checkbox.checked = false;
  }, false);
})(document);

document.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('theme-toggle-btn');
  if(btn) {
    btn.addEventListener('click', function() {
      document.body.classList.toggle('dark-theme');
    });
  }
});
