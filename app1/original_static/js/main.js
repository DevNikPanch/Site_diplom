var photos = [
    "./images/slider-1.webp",
    "./images/slider-2.webp",

]

document.querySelector("#image1").src = photos[0];
var i = 1;
setInterval(function() {
    document.querySelector("#image1").src = photos[i];
    ++i;
    if (i > photos.length - 1) {
        i = 0
    }
}, 1000);