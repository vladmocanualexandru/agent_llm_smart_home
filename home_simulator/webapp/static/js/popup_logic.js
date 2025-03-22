document.addEventListener("DOMContentLoaded", function() {
    const popup = document.getElementById('popup');
    const popupHeader = document.getElementById('popup_header');
    const closePopup = document.getElementById('close_popup');

    let isDragging = false;
    let offsetX, offsetY;

    popupHeader.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - popup.offsetLeft;
        offsetY = e.clientY - popup.offsetTop;
    });

    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            popup.style.left = `${e.clientX - offsetX}px`;
            popup.style.top = `${e.clientY - offsetY}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
});