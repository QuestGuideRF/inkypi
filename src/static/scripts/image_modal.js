document.addEventListener('DOMContentLoaded', function() {
    const imageContainer = document.querySelector('.image-container');
    const img = imageContainer.querySelector('img');
    let modalOverlay = null;
    let modalImg = null;
    let observer = null;
    if (!imageContainer || !img) return;
    img.addEventListener('click', function(e) {
        e.stopPropagation();
        modalOverlay = document.createElement('div');
        modalOverlay.className = 'image-modal-overlay';
        modalImg = document.createElement('img');
        modalImg.src = img.src;
        modalOverlay.appendChild(modalImg);
        document.body.appendChild(modalOverlay);
        imageContainer.classList.add('maximized');
        document.body.style.overflow = 'hidden';
        observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'src' && modalImg) {
                    modalImg.src = img.src;
                }
            });
        });
        observer.observe(img, { attributes: true, attributeFilter: ['src'] });
    });
    document.addEventListener('click', function(e) {
        if (imageContainer.classList.contains('maximized') && modalOverlay && !img.contains(e.target)) {
            if (observer) {
                observer.disconnect();
                observer = null;
            }
            modalOverlay.remove();
            modalOverlay = null;
            modalImg = null;
            imageContainer.classList.remove('maximized');
            document.body.style.overflow = '';
        }
    });
});