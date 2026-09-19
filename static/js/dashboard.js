function wrapDashboardLabel(label, maxLength = 24) {
    if (!label || label.length <= maxLength) return label;

    const words = label.split(" ");
    const lines = [];
    let current = "";

    words.forEach((word) => {
        const candidate = current ? `${current} ${word}` : word;
        if (candidate.length > maxLength && current) {
            lines.push(current);
            current = word;
        } else {
            current = candidate;
        }
    });

    if (current) lines.push(current);
    return lines;
}

function dashboardBaseOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 450,
        },
        plugins: {
            legend: {
                labels: {
                    boxWidth: 12,
                    boxHeight: 12,
                    usePointStyle: true,
                    pointStyle: "circle",
                    font: {
                        size: 11,
                    },
                },
            },
            tooltip: {
                displayColors: false,
            },
        },
    };
}

function percentageScale() {
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

function enableCompetitionDashboard() {
    const dataElement = document.getElementById("competition-dashboard-data");
    if (!dataElement || typeof Chart === "undefined") return;

    const data = JSON.parse(dataElement.textContent);
    const labels = data.disciplines.map((label) => wrapDashboardLabel(label));

    const progressCanvas = document.getElementById("lesson-progress-chart");
    if (progressCanvas) {
        new Chart(progressCanvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Aulas concluídas",
                    data: data.lesson_progress,
                    backgroundColor: "rgba(37, 99, 235, .72)",
                    borderRadius: 6,
                    barThickness: 18,
                }],
            },
            options: {
                ...dashboardBaseOptions(),
                indexAxis: "y",
                scales: {
                    x: percentageScale(),
                    y: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            autoSkip: false,
                            font: {
                                size: 11,
                            },
                        },
                    },
                },
                plugins: {
                    ...dashboardBaseOptions().plugins,
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                return `${context.raw}% concluído`;
                            },
                        },
                    },
                },
            },
        });
    }

    const statusCanvas = document.getElementById("lesson-status-chart");
    if (statusCanvas) {
        new Chart(statusCanvas, {
            type: "doughnut",
            data: {
                labels: data.status.labels,
                datasets: [{
                    data: data.status.values,
                    backgroundColor: [
                        "rgba(22, 163, 74, .78)",
                        "rgba(217, 119, 6, .78)",
                        "rgba(100, 116, 139, .55)",
                    ],
                    borderWidth: 0,
                    hoverOffset: 4,
                }],
            },
            options: {
                ...dashboardBaseOptions(),
                cutout: "68%",
                plugins: {
                    ...dashboardBaseOptions().plugins,
                    legend: {
                        position: "bottom",
                        labels: {
                            boxWidth: 10,
                            boxHeight: 10,
                            usePointStyle: true,
                            pointStyle: "circle",
                            padding: 14,
                            font: {
                                size: 11,
                            },
                        },
                    },
                },
            },
        });
    }

    const accuracyCanvas = document.getElementById("accuracy-chart");
    if (accuracyCanvas) {
        new Chart(accuracyCanvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "% de acerto",
                    data: data.accuracy,
                    backgroundColor: "rgba(14, 116, 144, .72)",
                    borderRadius: 6,
                    barThickness: 18,
                }],
            },
            options: {
                ...dashboardBaseOptions(),
                indexAxis: "y",
                scales: {
                    x: percentageScale(),
                    y: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            autoSkip: false,
                            font: {
                                size: 11,
                            },
                        },
                    },
                },
                plugins: {
                    ...dashboardBaseOptions().plugins,
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                if (context.raw === null) return "Sem questões";
                                return `${context.raw}% de acerto`;
                            },
                        },
                    },
                },
            },
        });
    }

    const coverageCanvas = document.getElementById("syllabus-coverage-chart");
    if (coverageCanvas) {
        new Chart(coverageCanvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Cobertura do edital",
                    data: data.syllabus_coverage,
                    backgroundColor: "rgba(124, 58, 237, .66)",
                    borderRadius: 6,
                    barThickness: 18,
                }],
            },
            options: {
                ...dashboardBaseOptions(),
                indexAxis: "y",
                scales: {
                    x: percentageScale(),
                    y: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            autoSkip: false,
                            font: {
                                size: 11,
                            },
                        },
                    },
                },
                plugins: {
                    ...dashboardBaseOptions().plugins,
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                return `${context.raw}% coberto`;
                            },
                        },
                    },
                },
            },
        });
    }

    const weeklyCanvas = document.getElementById("weekly-chart");
    if (weeklyCanvas) {
        new Chart(weeklyCanvas, {
            type: "bar",
            data: {
                labels: data.weeks.labels,
                datasets: [
                    {
                        label: "Aulas previstas",
                        data: data.weeks.total,
                        backgroundColor: "rgba(148, 163, 184, .45)",
                        borderRadius: 5,
                    },
                    {
                        label: "Concluídas",
                        data: data.weeks.completed,
                        backgroundColor: "rgba(37, 99, 235, .72)",
                        borderRadius: 5,
                    },
                ],
            },
            options: {
                ...dashboardBaseOptions(),
                scales: {
                    x: {
                        grid: {
                            display: false,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                        },
                        grid: {
                            color: "rgba(148, 163, 184, .16)",
                        },
                    },
                },
                plugins: {
                    ...dashboardBaseOptions().plugins,
                    legend: {
                        position: "bottom",
                        labels: {
                            boxWidth: 10,
                            boxHeight: 10,
                            usePointStyle: true,
                            pointStyle: "circle",
                            padding: 16,
                            font: {
                                size: 11,
                            },
                        },
                    },
                },
            },
        });
    }
}

document.addEventListener("DOMContentLoaded", enableCompetitionDashboard);
