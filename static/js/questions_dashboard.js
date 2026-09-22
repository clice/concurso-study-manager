function compactQuestionDashboardLabel(label, maxLength = 30) {
    if (!label || label.length <= maxLength) return label;
    return `${label.slice(0, maxLength - 1).trimEnd()}…`;
}

function questionDashboardBaseOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: {duration: 450},
        plugins: {
            legend: {
                labels: {
                    boxWidth: 10,
                    boxHeight: 10,
                    usePointStyle: true,
                    pointStyle: "circle",
                    font: {size: 11},
                },
            },
        },
    };
}

function percentageAxis() {
    return {
        beginAtZero: true,
        max: 100,
        ticks: {
            callback(value) {
                return `${value}%`;
            },
        },
        grid: {
            color: "rgba(148, 163, 184, .16)",
        },
    };
}

function enableGlobalQuestionDashboard() {
    const dataElement = document.getElementById("global-question-dashboard-data");
    if (!dataElement || typeof Chart === "undefined") return;

    const data = JSON.parse(dataElement.textContent);

    const volumeCanvas = document.getElementById("questions-over-time-chart");
    if (volumeCanvas) {
        new Chart(volumeCanvas, {
            type: "line",
            data: {
                labels: data.months.labels,
                datasets: [{
                    label: "Questões respondidas",
                    data: data.months.questions,
                    borderColor: "rgba(37, 99, 235, .85)",
                    backgroundColor: "rgba(37, 99, 235, .12)",
                    fill: true,
                    tension: .25,
                    pointRadius: 3,
                }],
            },
            options: {
                ...questionDashboardBaseOptions(),
                scales: {
                    x: {grid: {display: false}},
                    y: {
                        beginAtZero: true,
                        ticks: {precision: 0},
                        grid: {color: "rgba(148, 163, 184, .16)"},
                    },
                },
                plugins: {
                    ...questionDashboardBaseOptions().plugins,
                    legend: {display: false},
                },
            },
        });
    }

    const accuracyCanvas = document.getElementById("accuracy-over-time-chart");
    if (accuracyCanvas) {
        new Chart(accuracyCanvas, {
            type: "line",
            data: {
                labels: data.months.labels,
                datasets: [{
                    label: "% de acerto",
                    data: data.months.accuracy,
                    borderColor: "rgba(14, 116, 144, .85)",
                    backgroundColor: "rgba(14, 116, 144, .10)",
                    fill: true,
                    tension: .25,
                    pointRadius: 3,
                }],
            },
            options: {
                ...questionDashboardBaseOptions(),
                scales: {
                    x: {grid: {display: false}},
                    y: percentageAxis(),
                },
                plugins: {
                    ...questionDashboardBaseOptions().plugins,
                    legend: {display: false},
                    tooltip: {
                        callbacks: {
                            label(context) {
                                if (context.raw === null) return "Sem questões contabilizadas";
                                return `${context.raw}% de acerto`;
                            },
                        },
                    },
                },
            },
        });
    }

    const resultCanvas = document.getElementById("question-results-chart");
    if (resultCanvas) {
        new Chart(resultCanvas, {
            type: "doughnut",
            data: {
                labels: data.results.labels,
                datasets: [{
                    data: data.results.values,
                    backgroundColor: [
                        "rgba(22, 163, 74, .78)",
                        "rgba(220, 38, 38, .72)",
                        "rgba(100, 116, 139, .55)",
                    ],
                    borderWidth: 0,
                    hoverOffset: 4,
                }],
            },
            options: {
                ...questionDashboardBaseOptions(),
                cutout: "68%",
                plugins: {
                    ...questionDashboardBaseOptions().plugins,
                    legend: {
                        position: "bottom",
                        labels: {
                            boxWidth: 10,
                            boxHeight: 10,
                            usePointStyle: true,
                            pointStyle: "circle",
                            padding: 14,
                            font: {size: 11},
                        },
                    },
                },
            },
        });
    }

    const contestCanvas = document.getElementById("accuracy-by-contest-chart");
    if (contestCanvas) {
        const labels = data.contests.labels.map((label) =>
            compactQuestionDashboardLabel(label)
        );
        new Chart(contestCanvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "% de acerto",
                    data: data.contests.accuracy,
                    backgroundColor: "rgba(124, 58, 237, .68)",
                    borderRadius: 6,
                    barThickness: 18,
                }],
            },
            options: {
                ...questionDashboardBaseOptions(),
                indexAxis: "y",
                scales: {
                    x: percentageAxis(),
                    y: {
                        grid: {display: false},
                        ticks: {autoSkip: false, font: {size: 11}},
                    },
                },
                plugins: {
                    ...questionDashboardBaseOptions().plugins,
                    legend: {display: false},
                    tooltip: {
                        callbacks: {
                            title(items) {
                                if (!items.length) return "";
                                return data.contests.labels[items[0].dataIndex];
                            },
                            label(context) {
                                if (context.raw === null) return "Sem questões contabilizadas";
                                const total = data.contests.questions[context.dataIndex];
                                return `${context.raw}% · ${total} questões`;
                            },
                        },
                    },
                },
            },
        });
    }

    const disciplineCanvas = document.getElementById("accuracy-by-discipline-chart");
    if (disciplineCanvas) {
        const labels = data.disciplines.labels.map((label) =>
            compactQuestionDashboardLabel(label)
        );
        new Chart(disciplineCanvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "% de acerto",
                    data: data.disciplines.accuracy,
                    backgroundColor: "rgba(37, 99, 235, .72)",
                    borderRadius: 6,
                    barThickness: 18,
                }],
            },
            options: {
                ...questionDashboardBaseOptions(),
                indexAxis: "y",
                scales: {
                    x: percentageAxis(),
                    y: {
                        grid: {display: false},
                        ticks: {autoSkip: false, font: {size: 11}},
                    },
                },
                plugins: {
                    ...questionDashboardBaseOptions().plugins,
                    legend: {display: false},
                    tooltip: {
                        callbacks: {
                            title(items) {
                                if (!items.length) return "";
                                return data.disciplines.labels[items[0].dataIndex];
                            },
                            label(context) {
                                if (context.raw === null) return "Sem questões contabilizadas";
                                const total = data.disciplines.questions[context.dataIndex];
                                return `${context.raw}% · ${total} questões`;
                            },
                        },
                    },
                },
            },
        });
    }
}

document.addEventListener("DOMContentLoaded", enableGlobalQuestionDashboard);
