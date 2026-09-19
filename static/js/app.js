function formatBRLFromDigits(digits) {
    if (!digits) return "";

    const cents = digits.slice(-2).padStart(2, "0");
    let integer = digits.slice(0, -2) || "0";
    integer = integer.replace(/^0+(?=\d)/, "");
    integer = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

    return `R$ ${integer},${cents}`;
}

function getCookie(name) {
    const cookie = document.cookie
        .split(";")
        .map((item) => item.trim())
        .find((item) => item.startsWith(`${name}=`));

    return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
}

async function persistOrder(list) {
    const url = list.dataset.reorderUrl;
    if (!url) return;

    const order = Array.from(list.querySelectorAll("[data-sortable-item]"))
        .map((item) => Number(item.dataset.id));

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({order}),
    });

    if (!response.ok) {
        throw new Error("Não foi possível salvar a nova ordem.");
    }
}

function enableSortableLists() {
    document.querySelectorAll("[data-sortable-list]").forEach((list) => {
        let draggedItem = null;

        list.addEventListener("dragstart", (event) => {
            const handle = event.target.closest("[data-drag-handle]");
            if (!handle) {
                event.preventDefault();
                return;
            }

            draggedItem = handle.closest("[data-sortable-item]");
            if (!draggedItem) return;

            draggedItem.classList.add("dragging");
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", draggedItem.dataset.id);
        });

        list.addEventListener("dragover", (event) => {
            if (!draggedItem) return;
            event.preventDefault();

            const candidates = Array.from(
                list.querySelectorAll("[data-sortable-item]:not(.dragging)")
            );

            const nextItem = candidates.find((candidate) => {
                const box = candidate.getBoundingClientRect();
                return event.clientY < box.top + box.height / 2;
            });

            if (nextItem) {
                list.insertBefore(draggedItem, nextItem);
            } else {
                list.appendChild(draggedItem);
            }
        });

        list.addEventListener("dragend", async () => {
            if (!draggedItem) return;

            draggedItem.classList.remove("dragging");
            draggedItem = null;

            try {
                await persistOrder(list);
            } catch (error) {
                window.alert(error.message);
                window.location.reload();
            }
        });
    });
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

    enableSortableLists();
});
