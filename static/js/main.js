// Load and display basic statistics with brand and country data
Promise.all([
    fetch('/api/basic_stats').then(response => response.json()),
    fetch('/api/brand_stats').then(response => response.json()),
    fetch('/api/warehouse_countries').then(response => response.json())
])
    .then(([basicData, brandData, countryData]) => {
        const basicStatsDiv = document.getElementById('basic-stats');
        const contentDiv = basicStatsDiv.querySelector('.stat-content');
        
        // Format brand data
        const brands = brandData.brands;
        const brandText = brands.map(brand => {
            const percentage = ((brand.count / basicData.product_count) * 100).toFixed(1);
            return `${brand.name}: ${brand.count} (${percentage}%)`;
        }).join('<br>');
        
        // Format country data
        const countries = countryData.countries;
        const totalWarehouses = basicData.warehouse_count;
        const countryText = countries.map(country => {
            const percentage = ((country.count / totalWarehouses) * 100).toFixed(1);
            return `${country.name}: ${country.count} (${percentage}%)`;
        }).join('<br>');
        
        contentDiv.innerHTML = `
            <div class="stat-item">
                <strong>Almacenes:</strong> ${basicData.warehouse_count}
            </div>
            <div class="stat-item">
                <strong>Productos:</strong> ${basicData.product_count}
            </div>
            <div class="stat-item">
                <strong>Tiendas:</strong> ${basicData.store_count}
            </div>
            
            <div class="stat-divider"></div>
            
            <div class="stat-item">
                <strong>Distribución de Marcas:</strong><br>
                ${brandText}
            </div>
            
            <div class="stat-divider"></div>
            
            <div class="stat-item">
                <strong>Principales Países con Almacenes:</strong><br>
                ${countryText}
            </div>
        `;
    })
    .catch(error => console.error('Error al cargar las estadísticas:', error));

// Create size chart
fetch('/api/inventory_by_size')
    .then(response => response.json())
    .then(data => {
        const sizes = data.sizes.slice(0, 8); // Show only top 8 sizes
        const ctx = document.getElementById('sizeChart').getContext('2d');
        
        // Check if we're on mobile
        const isMobile = window.innerWidth < 768;
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sizes.map(size => size.size),
                datasets: [{
                    data: sizes.map(size => size.quantity),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)',
                        'rgba(201, 203, 207, 0.7)',
                        'rgba(255, 99, 71, 0.7)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)',
                        'rgba(201, 203, 207, 1)',
                        'rgba(255, 99, 71, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: isMobile ? 'bottom' : 'right',
                        labels: {
                            boxWidth: isMobile ? 12 : 20,
                            padding: isMobile ? 10 : 20,
                            font: {
                                size: isMobile ? 10 : 12
                            }
                        }
                    },
                    tooltip: {
                        bodyFont: {
                            size: isMobile ? 11 : 14
                        },
                        titleFont: {
                            size: isMobile ? 11 : 14
                        }
                    }
                }
            }
        });
    })
    .catch(error => console.error('Error al cargar datos de tallas:', error));

// Display top products table
fetch('/api/top_products')
    .then(response => response.json())
    .then(data => {
        const products = data.products;
        const tableContainer = document.getElementById('top-products-table');
        
        let tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID de Producto</th>
                        <th>Cantidad Total</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        products.forEach(product => {
            tableHTML += `
                <tr>
                    <td>${product.id}</td>
                    <td>${product.quantity}</td>
                </tr>
            `;
        });
        
        tableHTML += `
                </tbody>
            </table>
        `;
        
        tableContainer.innerHTML = tableHTML;
    })
    .catch(error => console.error('Error al cargar productos principales:', error));

// Gemini AI Question Interface
document.addEventListener('DOMContentLoaded', () => {
    const questionInput = document.getElementById('question-input');
    const askButton = document.getElementById('ask-button');
    const responseContainer = document.getElementById('gemini-response');
    const insightsContainer = document.getElementById('insights-container');
    const warehouseSelector = document.getElementById('warehouse-selector');
    const shipmentsContainer = document.getElementById('warehouse-shipments');
    
    // Function to ask a question
    async function askQuestion() {
        const question = questionInput.value.trim();
        if (!question) return;
        
        responseContainer.innerHTML = '<div class="loading"></div>';
        
        try {
            const response = await fetch('/api/ask_gemini', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question })
            });
            
            const data = await response.json();
            
            if (data.error) {
                responseContainer.innerHTML = `<p class="error">${data.error}</p>`;
            } else {
                // Use innerHTML to render the HTML content returned
                responseContainer.innerHTML = `<div class="markdown-content">${data.answer}</div>`;
            }
        } catch (error) {
            console.error('Error al consultar a Gemini:', error);
            responseContainer.innerHTML = `<p class="error">Error al procesar la consulta. Por favor, inténtalo de nuevo.</p>`;
        }
    }
    
    // Add event listeners
    askButton.addEventListener('click', askQuestion);
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            askQuestion();
        }
    });
    
    // Load AI insights
    fetch('/api/get_insights')
        .then(response => response.json())
        .then(data => {
            // Use innerHTML to render the HTML content
            insightsContainer.innerHTML = `<div class="markdown-content">${data.insights}</div>`;
        })
        .catch(error => {
            console.error('Error al cargar insights:', error);
            insightsContainer.innerHTML = '<p>No se pudieron cargar los insights.</p>';
        });
    
    // Load warehouse options for the selector
    fetch('/api/warehouse_shipments')
        .then(response => response.json())
        .then(data => {
            const warehouses = data.almacenes || [];
            
            // Create options for each warehouse
            warehouses.forEach(warehouse => {
                const option = document.createElement('option');
                option.value = warehouse.almacen;
                option.textContent = `${warehouse.almacen} (${warehouse.envios.length} envíos)`;
                warehouseSelector.appendChild(option);
            });
            
            // Enable selector if warehouses are available
            if (warehouses.length > 0) {
                warehouseSelector.disabled = false;
            } else {
                shipmentsContainer.innerHTML = '<p>No hay datos de envío disponibles.</p>';
            }
        })
        .catch(error => {
            console.error('Error al cargar los almacenes:', error);
            shipmentsContainer.innerHTML = '<p class="error">Error al cargar los datos de almacenes.</p>';
        });
    
    // Handle warehouse selection
    warehouseSelector.addEventListener('change', () => {
        const selectedWarehouse = warehouseSelector.value;
        
        if (!selectedWarehouse) {
            shipmentsContainer.innerHTML = '<p class="prompt-text">Seleccione un almacén para ver sus envíos a tiendas</p>';
            return;
        }
        
        shipmentsContainer.innerHTML = '<div class="loading"></div>';
        
        fetch(`/api/warehouse_shipments/${selectedWarehouse}`)
            .then(response => response.json())
            .then(data => {
                const envios = data.envios || [];
                
                if (envios.length === 0) {
                    shipmentsContainer.innerHTML = '<p>Este almacén no tiene envíos registrados.</p>';
                    return;
                }
                
                let shipmentHTML = '<div class="shipments-summary-container">';
                
                // Add summary statistics
                shipmentHTML += `
                    <div class="summary-stats">
                        <div class="summary-stat">
                            <span class="stat-value">${envios.length}</span>
                            <span class="stat-label">Tiendas Abastecidas</span>
                        </div>
                `;
                
                // Calculate total products and unique products counts
                let totalProducts = 0;
                let allProductIds = new Set();
                let allSizesCount = 0;
                
                envios.forEach(envio => {
                    totalProducts += envio.productos.length;
                    envio.productos.forEach(producto => {
                        allProductIds.add(producto.producto);
                        allSizesCount += producto.tallas.length;
                    });
                });
                
                // Add more stat boxes
                shipmentHTML += `
                        <div class="summary-stat">
                            <span class="stat-value">${allProductIds.size}</span>
                            <span class="stat-label">Productos Únicos</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-value">${totalProducts}</span>
                            <span class="stat-label">Total Productos Enviados</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-value">${allSizesCount}</span>
                            <span class="stat-label">Total Tallas Enviadas</span>
                        </div>
                    </div>
                `;
                
                // Create a summary table showing store ID and product counts
                shipmentHTML += `
                    <h3>Resumen de Envíos</h3>
                    <table class="shipments-table">
                        <thead>
                            <tr>
                                <th>Tienda</th>
                                <th>Productos Enviados</th>
                                <th>Total Tallas</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                envios.forEach(envio => {
                    const tiendaId = envio.tienda;
                    const productos = envio.productos || [];
                    
                    // Count total sizes across all products
                    let totalSizes = 0;
                    productos.forEach(producto => {
                        totalSizes += producto.tallas.length;
                    });
                    
                    shipmentHTML += `
                        <tr>
                            <td>${tiendaId}</td>
                            <td>${productos.length}</td>
                            <td>${totalSizes}</td>
                        </tr>
                    `;
                });
                
                shipmentHTML += `
                        </tbody>
                    </table>
                `;
                
                // Add product summary - most sent products
                let productCounts = {};
                envios.forEach(envio => {
                    envio.productos.forEach(producto => {
                        const productoId = producto.producto;
                        productCounts[productoId] = (productCounts[productoId] || 0) + 1;
                    });
                });
                
                // Convert to array and sort by frequency
                const sortedProducts = Object.entries(productCounts)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5); // Show top 5
                
                if (sortedProducts.length > 0) {
                    shipmentHTML += `
                        <h3>Productos Más Enviados</h3>
                        <table class="shipments-table">
                            <thead>
                                <tr>
                                    <th>ID Producto</th>
                                    <th>Enviado a # Tiendas</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    sortedProducts.forEach(([productId, count]) => {
                        shipmentHTML += `
                            <tr>
                                <td>${productId}</td>
                                <td>${count}</td>
                            </tr>
                        `;
                    });
                    
                    shipmentHTML += `
                            </tbody>
                        </table>
                    `;
                }
                
                // Add sizes summary
                const sizeCounts = {};
                envios.forEach(envio => {
                    envio.productos.forEach(producto => {
                        producto.tallas.forEach(talla => {
                            sizeCounts[talla] = (sizeCounts[talla] || 0) + 1;
                        });
                    });
                });
                
                // Convert to array and sort by frequency
                const sortedSizes = Object.entries(sizeCounts)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 10); // Show top 10 sizes
                
                if (sortedSizes.length > 0) {
                    shipmentHTML += `
                        <h3>Tallas Más Enviadas</h3>
                        <div class="sizes-bar-chart">
                    `;
                    
                    // Find max count for scaling
                    const maxCount = Math.max(...sortedSizes.map(s => s[1]));
                    
                    sortedSizes.forEach(([size, count]) => {
                        const percentage = Math.round((count / maxCount) * 100);
                        shipmentHTML += `
                            <div class="size-bar-item">
                                <div class="size-label">${size}</div>
                                <div class="size-bar-container">
                                    <div class="size-bar" style="width: ${percentage}%;">
                                        <span class="size-count">${count}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    shipmentHTML += `
                        </div>
                    `;
                }
                
                shipmentHTML += '</div>';
                shipmentsContainer.innerHTML = shipmentHTML;
            })
            .catch(error => {
                console.error('Error al cargar los envíos:', error);
                shipmentsContainer.innerHTML = '<p class="error">Error al cargar los datos de envíos.</p>';
            });
    });
    
    // Listen for window resize to adjust chart display
    window.addEventListener('resize', () => {
        // Refresh page on orientation change for better chart rendering
        // This is a simple solution - in a production app, we would just redraw the charts
        if (window.innerWidth !== window.lastWidth) {
            window.lastWidth = window.innerWidth;
            // Small delay to let resize complete
            setTimeout(() => {
                if (Math.abs(window.lastOrientation - window.orientation) === 90) {
                    window.location.reload();
                }
                window.lastOrientation = window.orientation;
            }, 150);
        }
    });
    
    // Store initial state
    window.lastWidth = window.innerWidth;
    window.lastOrientation = window.orientation || 0;
}); 