AOS.init({
    duration: 800,
    once: true
});

/* ==========================================
        ROI CALCULATOR
========================================== */

const rooms = document.getElementById("rooms");
const rent = document.getElementById("rent");

function updateROI() {

    if (!rooms || !rent) return;

    const monthly = Number(rooms.value) * Number(rent.value);
    const annual = monthly * 12;

    document.getElementById("monthlyRevenue").innerText =
        "₹" + monthly.toLocaleString("en-IN");

    document.getElementById("annualRevenue").innerText =
        "₹" + annual.toLocaleString("en-IN");

}

rooms.addEventListener("input", updateROI);
rent.addEventListener("input", updateROI);

updateROI();