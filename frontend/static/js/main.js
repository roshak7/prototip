// Функциональность интерфейса

// Переключение темы
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    
    // Проверка сохраненной темы в localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
        themeToggle.checked = true;
    }
    
    // Переключение темы
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
        
        // Обновляем цвета графиков при смене темы
        updateChartColors();
    });
    
    // Инициализация анимаций карточек KPI
    const kpiCards = document.querySelectorAll('.kpi-card');
    kpiCards.forEach(card => {
        card.classList.add('active');
    });
    
    // Функция применения фильтров
    const applyButton = document.getElementById('applyFilters');
    if (applyButton) {
        applyButton.addEventListener('click', function() {
            // Анимация нажатия кнопки
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 100);
            
            if (this.dataset.skipToast !== 'true') {
                showToast('Фильтры применены', 'success');
            }
            
            // Здесь будет логика обновления графиков
            // updateCharts();
        });
    }
    
    // Инициализация Chart.js графиков
    initCharts();
    
    // Инициализация всплывающих подсказок
    initTooltips();
    
    // Обработка изменения размера окна
    window.addEventListener('resize', function() {
        if (window.downtimeChart) {
            window.downtimeChart.resize();
        }
        if (window.productionChart) {
            window.productionChart.resize();
        }
        if (window.inventoryByCategoryChart) {
            window.inventoryByCategoryChart.resize();
        }
        if (window.shortageChart) {
            window.shortageChart.resize();
        }
        if (window.inventoryTrendChart) {
            window.inventoryTrendChart.resize();
        }
        if (window.turnoverChart) {
            window.turnoverChart.resize();
        }
    });
    
    // Обработка формы фильтров на дашборде
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        setupShopSelectionIndicator();

        // Отправляем форму при изменении любого фильтра
        const filterElements = filterForm.querySelectorAll('select, input');
        filterElements.forEach(element => {
            element.addEventListener('change', function() {
                // Дебаунс для предотвращения частых запросов
                clearTimeout(window.filterTimeout);
                window.filterTimeout = setTimeout(() => {
                    updateDashboardData();
                }, 300);
            });
        });
        
        // Обработчик кнопки сброса фильтров
        const resetButton = document.getElementById('resetFilters');
        if (resetButton) {
            resetButton.addEventListener('click', function() {
                // Сбрасываем все фильтры к значениям по умолчанию
                document.getElementById('period').value = 'month';
                
                // Снимаем выделение со всех цехов
                const shopSelect = document.getElementById('shop');
                for (let i = 0; i < shopSelect.options.length; i++) {
                    shopSelect.options[i].selected = false;
                }
                
                // Ставим галочки на все индикаторы по умолчанию
                const indicators = document.querySelectorAll('input[name="indicator"]');
                indicators.forEach(indicator => {
                    indicator.checked = true;
                });
                
                // Обновляем индикатор выбора цехов
                updateShopSelectionIndicator();
                
                // Обновляем данные дашборда
                updateDashboardData();
                
                // Показываем уведомление
                showToast('Фильтры сброшены', 'info');
            });
        }
    }

    initInventoryPage();
});

function initInventoryPage() {
    const filtersForm = document.getElementById('inventoryFilters');
    if (!filtersForm) {
        return;
    }

    const applyButton = document.getElementById('applyFilters');
    const resetButton = document.getElementById('resetInventoryFilters');
    const endpoint = filtersForm.dataset.endpoint;
    const initialData = window.INVENTORY_INITIAL_DATA || null;

    if (initialData) {
        renderInventoryData(initialData);
    }

    filtersForm.addEventListener('submit', function(event) {
        event.preventDefault();
        fetchInventoryData(filtersForm, endpoint, applyButton);
    });

    if (applyButton) {
        applyButton.addEventListener('click', function(event) {
            event.preventDefault();
            filtersForm.dispatchEvent(new Event('submit', { cancelable: true }));
        });
    }

    if (resetButton) {
        resetButton.addEventListener('click', function() {
            filtersForm.reset();
            updateShopSelectionIndicator();
            fetchInventoryData(filtersForm, endpoint, applyButton);
        });
    }

    setupShopSelectionIndicator();
}

function fetchInventoryData(form, endpoint, applyButton) {
    if (!endpoint) {
        return;
    }

    const params = new URLSearchParams(new FormData(form));

    if (applyButton) {
        applyButton.disabled = true;
        applyButton.classList.add('is-loading');
    }

    fetch(`${endpoint}?${params.toString()}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load inventory data');
            }
            return response.json();
        })
        .then(data => {
            renderInventoryData(data);
            showToast('Данные обновлены', 'success');
        })
        .catch(() => {
            showToast('Не удалось обновить данные склада', 'danger');
        })
        .finally(() => {
            if (applyButton) {
                applyButton.disabled = false;
                applyButton.classList.remove('is-loading');
            }
        });
}

function renderInventoryData(data) {
    if (!data) {
        return;
    }

    window.INVENTORY_INITIAL_DATA = data;

    updateInventorySummary(data.summary || {});
    updateInventoryTable((data.table && data.table.rows) || []);
    renderInventoryCharts(getChartColors(), data.charts || {});
}

function updateInventorySummary(summary) {
    setTextContent('inventoryTotalQuantity', formatInventoryNumber(summary.total_quantity) + ' ед.');
    setTextContent('inventoryDeficitPositions', formatInventoryNumber(summary.deficit_positions));
    setTextContent('inventoryTotalValue', formatInventoryCurrency(summary.total_value));
    setTextContent('inventoryAverageTurnover', formatInventoryNumber(summary.average_turnover, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' раз/мес');
}

function updateInventoryTable(rows) {
    const tbody = document.getElementById('inventoryTableBody');
    if (!tbody) {
        return;
    }

    tbody.innerHTML = '';

    if (!rows.length) {
        const emptyRow = document.createElement('tr');
        const emptyCell = document.createElement('td');
        emptyCell.colSpan = 10;
        emptyCell.className = 'text-center text-muted py-4';
        emptyCell.textContent = 'Нет данных за выбранный период';
        emptyRow.appendChild(emptyCell);
        tbody.appendChild(emptyRow);
        return;
    }

    rows.forEach(row => {
        const tr = document.createElement('tr');

        const cells = [
            row.sku,
            row.name,
            row.category,
            formatInventoryNumber(row.quantity),
            formatInventoryNumber(row.reserved),
            formatInventoryNumber(row.available),
            formatInventoryNumber(row.min_threshold),
            formatInventoryNumber(row.demand),
            formatInventoryNumber(row.shortage),
        ];

        cells.forEach((value, index) => {
            const td = document.createElement('td');
            td.textContent = value;
            if (index === 8 && Number(row.shortage) > 0) {
                td.classList.add('text-danger');
            }
            tr.appendChild(td);
        });

        const statusCell = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = `badge bg-${row.status_class || 'secondary'}`;
        badge.textContent = row.status || '—';
        statusCell.appendChild(badge);
        tr.appendChild(statusCell);

        tbody.appendChild(tr);
    });
}

function renderInventoryCharts(colors, chartsData) {
    const palette = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#8AC926', '#1982C4', '#6A4C93', '#2EC4B6'
    ];

    const createPalette = (length) => Array.from({ length }, (_, index) => palette[index % palette.length]);
    const ensureData = (labels, values) => {
        if (!labels.length) {
            labels.push('Нет данных');
            values.push(0);
        }
    };

    const byCategory = chartsData.inventory_by_category || [];
    const categoryLabels = byCategory.map(item => item.name);
    const categoryValues = byCategory.map(item => item.quantity);
    const categoryColors = categoryValues.length ? createPalette(categoryValues.length) : [palette[0]];
    ensureData(categoryLabels, categoryValues);

    const inventoryByCategoryCtx = document.getElementById('inventoryByCategoryChart');
    if (inventoryByCategoryCtx) {
        const chart = ensureChartInstance('inventoryByCategoryChart', inventoryByCategoryCtx, () => ({
            type: 'bar',
            data: {
                labels: [...categoryLabels],
                datasets: [{
                    label: 'Остатки, ед.',
                    data: [...categoryValues],
                    backgroundColor: [...categoryColors],
                    borderWidth: 0,
                }],
            },
            options: buildInventoryBarOptions(colors),
        }));

        chart.data.labels = categoryLabels;
        chart.data.datasets[0].data = categoryValues;
        chart.data.datasets[0].backgroundColor = categoryColors;
        chart.update();
    }

    const shortage = chartsData.shortage_by_category || [];
    const shortageLabels = shortage.map(item => item.name);
    const shortageValues = shortage.map(item => item.shortage);
    const shortageColors = shortageValues.length ? createPalette(shortageValues.length) : [palette[0]];
    ensureData(shortageLabels, shortageValues);
    const shortageCtx = document.getElementById('shortageChart');
    if (shortageCtx) {
        const chart = ensureChartInstance('shortageChart', shortageCtx, () => ({
            type: 'bar',
            data: {
                labels: [...shortageLabels],
                datasets: [{
                    label: 'Дефицит, ед.',
                    data: [...shortageValues],
                    backgroundColor: [...shortageColors],
                    borderWidth: 0,
                }],
            },
            options: buildInventoryBarOptions(colors),
        }));

        chart.data.labels = shortageLabels;
        chart.data.datasets[0].data = shortageValues;
        chart.data.datasets[0].backgroundColor = shortageColors;
        chart.update();
    }

    const trend = chartsData.inventory_trend || [];
    const trendLabels = trend.map(item => item.date);
    const trendQuantity = trend.map(item => item.quantity);
    const trendShortage = trend.map(item => item.shortage);
    ensureData(trendLabels, trendQuantity);
    if (trendShortage.length === 0) {
        trendShortage.push(0);
    }
    const trendCtx = document.getElementById('inventoryTrendChart');
    if (trendCtx) {
        const chart = ensureChartInstance('inventoryTrendChart', trendCtx, () => ({
            type: 'line',
            data: {
                labels: [...trendLabels],
                datasets: [
                    {
                        label: 'Остатки',
                        data: [...trendQuantity],
                        borderColor: '#4BC0C0',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: true,
                        tension: 0.4,
                    },
                    {
                        label: 'Дефицит',
                        data: [...trendShortage],
                        borderColor: '#FF6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: true,
                        tension: 0.4,
                    },
                ],
            },
            options: buildInventoryLineOptions(colors),
        }));

        chart.data.labels = trendLabels;
        chart.data.datasets[0].data = trendQuantity;
        chart.data.datasets[1].data = trendShortage;
        chart.update();
    }

    const turnover = chartsData.turnover_by_category || [];
    const turnoverLabels = turnover.map(item => item.name);
    const turnoverValues = turnover.map(item => item.turnover);
    const turnoverColors = turnoverValues.length ? createPalette(turnoverValues.length) : [palette[0]];
    ensureData(turnoverLabels, turnoverValues);
    const turnoverCtx = document.getElementById('turnoverChart');
    if (turnoverCtx) {
        const chart = ensureChartInstance('turnoverChart', turnoverCtx, () => ({
            type: 'bar',
            data: {
                labels: [...turnoverLabels],
                datasets: [{
                    label: 'Оборачиваемость, раз/мес',
                    data: [...turnoverValues],
                    backgroundColor: [...turnoverColors],
                    borderWidth: 0,
                }],
            },
            options: buildInventoryBarOptions(colors),
        }));

        chart.data.labels = turnoverLabels;
        chart.data.datasets[0].data = turnoverValues;
        chart.data.datasets[0].backgroundColor = turnoverColors;
        chart.update();
    }
}

function ensureChartInstance(refName, ctx, configFactory) {
    let chart = window[refName];

    if (!chart || !chart.data || !Array.isArray(chart.data.datasets)) {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }

        chart = new Chart(ctx, configFactory());
        window[refName] = chart;
    }

    return chart;
}

function buildInventoryBarOptions(colors) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: colors.textColor,
                    font: {
                        size: 12,
                    },
                },
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: colors.gridColor,
                },
                ticks: {
                    color: colors.textColor,
                    font: {
                        size: 11,
                    },
                },
            },
            x: {
                grid: {
                    color: colors.gridColor,
                },
                ticks: {
                    color: colors.textColor,
                    font: {
                        size: 11,
                    },
                },
            },
        },
        animation: {
            duration: 800,
            easing: 'easeInOutQuart',
        },
    };
}

function buildInventoryLineOptions(colors) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: colors.textColor,
                    font: {
                        size: 12,
                    },
                },
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: colors.gridColor,
                },
                ticks: {
                    color: colors.textColor,
                    font: {
                        size: 11,
                    },
                },
            },
            x: {
                grid: {
                    color: colors.gridColor,
                },
                ticks: {
                    color: colors.textColor,
                    font: {
                        size: 11,
                    },
                },
            },
        },
        animation: {
            duration: 800,
            easing: 'easeInOutQuart',
        },
    };
}

function setTextContent(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function formatInventoryNumber(value, options = {}) {
    const formatter = new Intl.NumberFormat('ru-RU', options);
    const numericValue = Number.isFinite(Number(value)) ? Number(value) : 0;
    return formatter.format(numericValue);
}

function formatInventoryCurrency(value) {
    const formatter = new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        maximumFractionDigits: 0,
    });
    const numericValue = Number.isFinite(Number(value)) ? Number(value) : 0;
    return formatter.format(numericValue);
}

function setupShopSelectionIndicator() {
    const shopSelect = document.getElementById('shop');
    if (!shopSelect) {
        return;
    }

    updateShopSelectionIndicator();
    shopSelect.addEventListener('change', updateShopSelectionIndicator);
}

function updateShopSelectionIndicator() {
    const shopSelect = document.getElementById('shop');
    const indicator = document.getElementById('shopSelectionIndicator') || document.getElementById('shop-selection-indicator');

    if (!shopSelect || !indicator) {
        return;
    }

    const selectedOption = shopSelect.value;
    if (!selectedOption) {
        indicator.textContent = 'Выбраны все цеха';
    } else {
        const selectedText = shopSelect.options[shopSelect.selectedIndex]?.text || 'Цех';
        indicator.textContent = `Выбран: ${selectedText}`;
    }
}

// Получение цветов для графиков в зависимости от темы
function getChartColors() {
    const isDarkTheme = document.body.classList.contains('dark-theme');
    return {
        textColor: isDarkTheme ? '#E2E8F0' : '#1F1F1F',
        gridColor: isDarkTheme ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        backgroundColor: isDarkTheme ? '#1A202C' : '#FFFFFF'
    };
}

// Обновление цветов графиков при смене темы
function updateChartColors() {
    const colors = getChartColors();
    
    if (window.downtimeChart) {
        window.downtimeChart.options.scales.x.ticks.color = colors.textColor;
        window.downtimeChart.options.scales.y.ticks.color = colors.textColor;
        window.downtimeChart.options.scales.x.grid.color = colors.gridColor;
        window.downtimeChart.options.scales.y.grid.color = colors.gridColor;
        window.downtimeChart.options.plugins.legend.labels.color = colors.textColor;
        window.downtimeChart.update();
    }
    
    if (window.productionChart) {
        window.productionChart.options.scales.x.ticks.color = colors.textColor;
        window.productionChart.options.scales.y.ticks.color = colors.textColor;
        window.productionChart.options.scales.x.grid.color = colors.gridColor;
        window.productionChart.options.scales.y.grid.color = colors.gridColor;
        window.productionChart.options.plugins.legend.labels.color = colors.textColor;
        window.productionChart.update();
    }
    
    if (window.inventoryByCategoryChart) {
        window.inventoryByCategoryChart.options.scales.x.ticks.color = colors.textColor;
        window.inventoryByCategoryChart.options.scales.y.ticks.color = colors.textColor;
        window.inventoryByCategoryChart.options.scales.x.grid.color = colors.gridColor;
        window.inventoryByCategoryChart.options.scales.y.grid.color = colors.gridColor;
        window.inventoryByCategoryChart.options.plugins.legend.labels.color = colors.textColor;
        window.inventoryByCategoryChart.update();
    }
    
    if (window.shortageChart) {
        window.shortageChart.options.scales.x.ticks.color = colors.textColor;
        window.shortageChart.options.scales.y.ticks.color = colors.textColor;
        window.shortageChart.options.scales.x.grid.color = colors.gridColor;
        window.shortageChart.options.scales.y.grid.color = colors.gridColor;
        window.shortageChart.options.plugins.legend.labels.color = colors.textColor;
        window.shortageChart.update();
    }
    
    if (window.inventoryTrendChart) {
        window.inventoryTrendChart.options.scales.x.ticks.color = colors.textColor;
        window.inventoryTrendChart.options.scales.y.ticks.color = colors.textColor;
        window.inventoryTrendChart.options.scales.x.grid.color = colors.gridColor;
        window.inventoryTrendChart.options.scales.y.grid.color = colors.gridColor;
        window.inventoryTrendChart.options.plugins.legend.labels.color = colors.textColor;
        window.inventoryTrendChart.update();
    }
    
    if (window.turnoverChart) {
        window.turnoverChart.options.scales.x.ticks.color = colors.textColor;
        window.turnoverChart.options.scales.y.ticks.color = colors.textColor;
        window.turnoverChart.options.scales.x.grid.color = colors.gridColor;
        window.turnoverChart.options.scales.y.grid.color = colors.gridColor;
        window.turnoverChart.options.plugins.legend.labels.color = colors.textColor;
        window.turnoverChart.update();
    }
}

// Инициализация графиков Chart.js
function initCharts() {
    const colors = getChartColors();
    
    // График простоев по цехам (столбчатая диаграмма)
    const downtimeCtx = document.getElementById('downtimeChart');
    if (downtimeCtx) {
        window.downtimeChart = new Chart(downtimeCtx, {
            type: 'bar',
            data: {
                labels: ["Цех 1", "Цех 2", "Цех 3", "Цех 4", "Цех 5"],
                datasets: [{
                    label: "Простои (часы)",
                    data: [5, 7, 8, 3, 6],
                    backgroundColor: [
                        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: colors.textColor,
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: colors.gridColor
                        },
                        ticks: {
                            color: colors.textColor,
                            font: {
                                size: 11
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: colors.gridColor
                        },
                        ticks: {
                            color: colors.textColor,
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }
    
    // График выпуска продукции за месяц (линейный график)
    const productionCtx = document.getElementById('productionChart');
    if (productionCtx) {
        window.productionChart = new Chart(productionCtx, {
            type: 'line',
            data: {
                labels: ["1", "5", "10", "15", "20", "25", "30"],
                datasets: [{
                    label: "Выпуск, ед.",
                    data: [200, 350, 400, 600, 550, 700, 800],
                    borderColor: "#4BC0C0",
                    backgroundColor: "rgba(75, 192, 192, 0.2)",
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: colors.textColor,
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: colors.gridColor
                        },
                        ticks: {
                            color: colors.textColor,
                            font: {
                                size: 11
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: colors.gridColor
                        },
                        ticks: {
                            color: colors.textColor,
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }
    
    // Функция для создания дополнительных графиков с новыми метриками
    function createAdditionalCharts() {
        // График остатков на складе
        const inventoryCtx = document.getElementById('inventoryChart');
        if (inventoryCtx) {
            window.inventoryChart = new Chart(inventoryCtx, {
                type: 'line',
                data: {
                    labels: ["1", "5", "10", "15", "20", "25", "30"],
                    datasets: [{
                        label: "Остатки на складе, ед.",
                        data: [15000, 14500, 16000, 15500, 14000, 15200, 14800],
                        borderColor: "#9966FF",
                        backgroundColor: "rgba(153, 102, 255, 0.2)",
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: colors.textColor,
                                font: {
                                    size: 12
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: colors.gridColor
                            },
                            ticks: {
                                color: colors.textColor,
                                font: {
                                    size: 11
                                }
                            }
                        },
                        x: {
                            grid: {
                                color: colors.gridColor
                            },
                            ticks: {
                                color: colors.textColor,
                                font: {
                                    size: 11
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart'
                    }
                }
            });
        }
        
        // График выполнения плана
        const planCtx = document.getElementById('planChart');
        if (planCtx) {
            window.planChart = new Chart(planCtx, {
                type: 'bar',
                data: {
                    labels: ["Цех 1", "Цех 2", "Цех 3", "Цех 4", "Цех 5"],
                    datasets: [{
                        label: "Выполнение плана, %",
                        data: [92, 88, 95, 85, 90],
                        backgroundColor: [
                            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: colors.textColor,
                                font: {
                                    size: 12
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: colors.gridColor
                            },
                            ticks: {
                                color: colors.textColor,
                                font: {
                                    size: 11
                                }
                            }
                        },
                        x: {
                            grid: {
                                color: colors.gridColor
                            },
                            ticks: {
                                color: colors.textColor,
                                font: {
                                    size: 11
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart'
                    }
                }
            });
        }
    }
    
    // Вызываем функцию создания дополнительных графиков
    createAdditionalCharts();
    
    // Графики для страницы склада
    initInventoryCharts(colors);
}

// Инициализация графиков для страницы склада
function initInventoryCharts(colors) {
    if (!window.INVENTORY_INITIAL_DATA || !window.INVENTORY_INITIAL_DATA.charts) {
        return;
    }

    renderInventoryCharts(colors, window.INVENTORY_INITIAL_DATA.charts);
}

// Функция обновления графиков (заглушка)
function updateCharts() {
    // Здесь будет логика обновления графиков при применении фильтров
    // Пока показываем уведомление
    showToast('Графики обновлены', 'success');
}

// Инициализация всплывающих подсказок
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            // Создание и отображение всплывающей подсказки
            // В реальной реализации здесь будет код для создания tooltip
        });
    });
}

// Показ уведомления (toast)
function showToast(message, type = 'info') {
    // Создание элемента уведомления
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            ${message}
        </div>
    `;
    
    // Добавление уведомления в документ
    document.body.appendChild(toast);
    
    // Показываем уведомление с анимацией
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Автоматическое удаление уведомления через 3 секунды
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, 3000);
}

// Функция для работы с выпадающими списками
function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// Закрытие выпадающих списков при клике вне их
document.addEventListener('click', function(event) {
    const dropdowns = document.querySelectorAll('.dropdown-content');
    dropdowns.forEach(dropdown => {
        if (!dropdown.parentElement.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    });
});

// Функция для работы с модальными окнами
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        // Предотвращаем прокрутку фона при открытом модальном окне
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        // Восстанавливаем прокрутку
        document.body.style.overflow = 'auto';
    }
}

// Закрытие модального окна при клике вне его содержимого
document.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
});

// Закрытие модального окна клавишей Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
});

// Дополнительные функции для формы авторизации и дашборда
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем анимацию для поля ввода на странице входа
    const loginInputs = document.querySelectorAll('.login-form .form-control');
    loginInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
    
    // Добавляем пульсацию для кнопки входа при загрузке
    const loginSubmitBtn = document.querySelector('.login-submit');
    if (loginSubmitBtn) {
        setTimeout(() => {
            if (loginSubmitBtn) {
                loginSubmitBtn.classList.add('pulse');
                setTimeout(() => {
                    if (loginSubmitBtn) {
                        loginSubmitBtn.classList.remove('pulse');
                    }
                }, 1000);
            }
        }, 500);
    }
    
    // Обработка формы фильтров на дашборде
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            // Анимация нажатия кнопки
            const applyButton = this.querySelector('.apply-button');
            if (applyButton) {
                applyButton.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    applyButton.style.transform = '';
                }, 100);
            }
            
            // Показ уведомления
            showToast('Фильтры применены', 'success');
        });
        
        // Добавляем обработчик для изменения фильтров (без отправки формы)
        const filterElements = filterForm.querySelectorAll('select, input');
        filterElements.forEach(element => {
            element.addEventListener('change', function() {
                // Обновляем URL с параметрами фильтрации
                updateDashboardData();
            });
        });
    }
    
    // Инициализация анимаций карточек KPI
    const kpiCards = document.querySelectorAll('.kpi-card');
    kpiCards.forEach((card, index) => {
        // Добавляем задержку для анимации появления
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('active');
    });
});

// Функция для обновления данных дашборда с фильтрацией
function updateDashboardData() {
    // Показываем индикатор загрузки
    showLoadingIndicator();
    
    // Получаем текущие значения фильтров
    const period = document.getElementById('period')?.value || 'month';
    const shopSelect = document.getElementById('shop');
    const selectedShops = Array.from(shopSelect.selectedOptions).map(option => option.value);
    const indicators = Array.from(document.querySelectorAll('input[name="indicator"]:checked')).map(cb => cb.value);
    
    // Формируем URL с параметрами
    let url = window.location.pathname;
    const params = new URLSearchParams();
    
    // Добавляем параметры только если они не равны значениям по умолчанию
    if (period !== 'month') {
        params.set('period', period);
    }
    
    selectedShops.forEach(shop => params.append('shop', shop));
    
    // Добавляем индикаторы только если они отличаются от всех выбранных
    const allIndicators = ['output', 'downtime', 'defect', 'load'];
    if (JSON.stringify(indicators.sort()) !== JSON.stringify(allIndicators.sort())) {
        indicators.forEach(indicator => params.append('indicator', indicator));
    }
    
    // Формируем новый URL
    const newUrl = params.toString() ? url + '?' + params.toString() : url;
    
    // Добавляем заголовок для AJAX-запроса
    fetch(newUrl, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Обновляем KPI-карточки
            document.querySelector('.kpi-cards').innerHTML = data.kpi_cards_html;
            
            // Обновляем графики с новыми данными
            if (window.updateChartsWithData) {
                window.updateChartsWithData(data.chart_data);
            }
            
            // Обновляем URL без перезагрузки
            window.history.pushState({}, '', newUrl);
            
            // Показываем уведомление об успешном обновлении
            showToast('Данные дашборда обновлены', 'success');
        })
        .catch(error => {
            console.error('Ошибка при обновлении данных дашборда:', error);
            // При ошибке перезагружаем страницу
            window.location.href = newUrl;
        })
        .finally(() => {
            // Скрываем индикатор загрузки
            hideLoadingIndicator();
        });
}

// Показываем индикатор загрузки
function showLoadingIndicator() {
    // Создаем оверлей с индикатором загрузки
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
        width: 50px;
        height: 50px;
        border: 5px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s linear infinite;
    `;
    
    overlay.appendChild(spinner);
    document.body.appendChild(overlay);
    
    // Добавляем анимацию вращения
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

// Скрываем индикатор загрузки
function hideLoadingIndicator() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}
