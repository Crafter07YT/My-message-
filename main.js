// Heart burst on click/touch
document.addEventListener("click", createHearts);
document.addEventListener("touchstart", createHearts);

function createHearts(e) {
    let x = e.touches ? e.touches[0].clientX : e.clientX;
    let y = e.touches ? e.touches[0].clientY : e.clientY;

    const emojis = ["💜","🌷","🤍"];

    for(let i=0;i<10;i++){
        let heart=document.createElement("div");
        heart.className="heart";
        heart.textContent=emojis[Math.floor(Math.random()*emojis.length)];

        heart.style.left = x + "px";
        heart.style.top = y + "px";

        let moveX = (Math.random()-0.5)*400 + "px";
        let moveY = (Math.random()-0.5)*400 + "px";

        heart.style.setProperty("--x", moveX);
        heart.style.setProperty("--y", moveY);

        document.body.appendChild(heart);

        setTimeout(()=>heart.remove(),2500);
    }
}

// Pop-in boxes with blur
const boxes = document.querySelectorAll('.msg-box');

const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if(entry.isIntersecting){
            entry.target.classList.add('show');
        } else {
            entry.target.classList.remove('show'); // allows re-animation
        }
    });
},{ threshold: 0.1 });

boxes.forEach(box => observer.observe(box));