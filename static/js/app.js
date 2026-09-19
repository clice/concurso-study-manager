function formatBRLFromDigits(digits) {
    if (!digits) return "";

    const cents = digits.slice(-2).padStart(2, "0");
    let integer = digits.slice(0, -2) || "0";
    integer = integer.replace(/^0+(?=\d)/, "");
    integer = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

    return `R$ ${integer},${cents}`;
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".money-input").forEach((input) => {
        input.addEventListener("input", () => {
            const digits = input.value.replace(/\D/g, "");
            input.value = formatBRLFromDigits(digits);
        });

        input.addEventListener("blur", () => {
            const digits = input.value.replace(/\D/g, "");
            if (digits) input.value = formatBRLFromDigits(digits);
        });
    });
});
