/* Called as soon as the unchanged reference script has initialized the site. */
window.initializePersonalSite = function () {
  'use strict';
  if (window.Widgets?.Sounds) {
    Widgets.Sounds.muted = true;
    document.body.classList.add('is-muted');
  }
  const notice = window.site?.cookies;
  if (!notice?.view) return;
  // Retain the original drop/swing animation, independently of cookie consent.
  notice.tryToShow = function () {
    if (this.view && !this.shown) this.show();
  };
  notice.view.find('.js-cookies-agree').off('click').on('click', event => {
    event.preventDefault();
    event.stopPropagation();
    notice.hide();
  });
  if (window.site.isReady) notice.tryToShow();
};
