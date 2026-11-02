const buttons = document.querySelectorAll(".demo-btn");

const image = document.getElementById("demoImage");

buttons.forEach(btn=>{

btn.onclick=()=>{

buttons.forEach(b=>b.classList.remove("active"));

btn.classList.add("active");

image.style.opacity=0;

setTimeout(()=>{

image.src=`assets/images/dashboard/${btn.dataset.image}.png`;

image.style.opacity=1;

},250);

}

});