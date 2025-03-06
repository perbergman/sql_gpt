// SQL-GPT Web Interface JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Use the stored instance or the global one
    const highlightJs = window.hljsInstance || window.hljs;
    
    // Initialize highlight.js if available
    if (typeof highlightJs !== 'undefined') {
        highlightJs.highlightAll();
        console.log('highlight.js initialized successfully');
    } else {
        console.warn('highlight.js not available, syntax highlighting disabled');
    }
    
    // Get DOM elements
    const promptForm = document.getElementById('prompt-form');
    const promptInput = document.getElementById('prompt');
    const resultsContainer = document.getElementById('results-container');
    const sqlContent = document.getElementById('sql-content');
    const intentContent = document.getElementById('intent-content');
    const deploymentContent = document.getElementById('deployment-content');
    const validationContent = document.getElementById('validation-content');
    const executionResults = document.getElementById('execution-results');
    const executionContent = document.getElementById('execution-content');
    const schemaContainer = document.getElementById('schema-container');
    const schemaContent = document.getElementById('schema-content');
    
    // Database browser elements
    const dbBrowserContainer = document.getElementById('db-browser-container');
    const tablesList = document.getElementById('tables-list');
    const selectedTableName = document.getElementById('selected-table-name');
    const tableStructureBtn = document.getElementById('table-structure-btn');
    const tableDataBtn = document.getElementById('table-data-btn');
    const tableStructureContainer = document.getElementById('table-structure-container');
    const tableDataContainer = document.getElementById('table-data-container');
    const tableInitialMessage = document.getElementById('table-initial-message');
    const tableStructureBody = document.getElementById('table-structure-body');
    const tableDataHeader = document.getElementById('table-data-header');
    const tableDataBody = document.getElementById('table-data-body');
    const tableDataPagination = document.getElementById('table-data-pagination');
    const tableDataLimit = document.getElementById('table-data-limit');
    const tableDataPrev = document.getElementById('table-data-prev');
    const tableDataNext = document.getElementById('table-data-next');
    
    // Check if all required elements are found
    const missingElements = [];
    if (!dbBrowserContainer) missingElements.push('db-browser-container');
    if (!tablesList) missingElements.push('tables-list');
    if (!selectedTableName) missingElements.push('selected-table-name');
    if (!tableStructureBtn) missingElements.push('table-structure-btn');
    if (!tableDataBtn) missingElements.push('table-data-btn');
    if (!tableStructureContainer) missingElements.push('table-structure-container');
    if (!tableDataContainer) missingElements.push('table-data-container');
    if (!tableInitialMessage) missingElements.push('table-initial-message');
    if (!tableStructureBody) missingElements.push('table-structure-body');
    if (!tableDataHeader) missingElements.push('table-data-header');
    if (!tableDataBody) missingElements.push('table-data-body');
    if (!tableDataPagination) missingElements.push('table-data-pagination');
    if (!tableDataLimit) missingElements.push('table-data-limit');
    if (!tableDataPrev) missingElements.push('table-data-prev');
    if (!tableDataNext) missingElements.push('table-data-next');
    
    if (missingElements.length > 0) {
        console.error('Missing DOM elements:', missingElements);
    }
    
    // Button event listeners
    document.getElementById('execute-sql-btn').addEventListener('click', executeSql);
    document.getElementById('copy-sql-btn').addEventListener('click', () => copyToClipboard(sqlContent.textContent));
    document.getElementById('copy-deployment-btn').addEventListener('click', () => copyToClipboard(deploymentContent.textContent));
    document.getElementById('test-connection-btn').addEventListener('click', testConnection);
    document.getElementById('view-schema-btn').addEventListener('click', viewSchema);
    document.getElementById('db-browser-btn').addEventListener('click', openDatabaseBrowser);
    document.getElementById('refresh-tables-btn').addEventListener('click', loadTables);
    tableStructureBtn.addEventListener('click', showTableStructure);
    tableDataBtn.addEventListener('click', showTableData);
    tableDataLimit.addEventListener('change', () => loadTableData(currentTable, currentSchema, 0));
    tableDataPrev.addEventListener('click', loadPreviousTableData);
    tableDataNext.addEventListener('click', loadNextTableData);
    
    // Form submission
    promptForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const prompt = promptInput.value.trim();
        if (!prompt) {
            showMessage('Error', 'Please enter a prompt.');
            return;
        }
        
        processPrompt(prompt);
    });
    
    // Process the prompt
    function processPrompt(prompt) {
        showLoading();
        console.log('Processing prompt:', prompt);
        
        // Debug information
        console.log('OpenAI API Key available:', !!window.openaiApiKey);
        console.log('Browser details:', navigator.userAgent);
        
        // Create a timestamp for tracking request timing
        const requestStartTime = new Date().getTime();
        
        fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt })
        })
        .then(response => {
            const requestEndTime = new Date().getTime();
            console.log(`Response received in ${requestEndTime - requestStartTime}ms`);
            console.log('Response status:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
            
            return response.text().then(text => {
                console.log('Raw response text:', text);
                
                // Try to parse as JSON, but handle parsing errors
                let data;
                try {
                    data = JSON.parse(text);
                    console.log('Parsed JSON data:', data);
                } catch (e) {
                    console.error('Failed to parse response as JSON:', e);
                    return { status: response.status, data: null, rawText: text, parseError: e.message };
                }
                
                return { status: response.status, data, rawText: text };
            });
        })
        .then(result => {
            hideLoading();
            const { status, data, rawText, parseError } = result;
            
            // Handle JSON parsing errors
            if (parseError) {
                console.error('JSON parse error:', parseError);
                console.log('Raw response that failed to parse:', rawText);
                showMessage('Error', 'Failed to parse server response. Check the console for details.');
                return;
            }
            
            console.log('Received data object type:', typeof data);
            console.log('Received data keys:', data ? Object.keys(data) : 'No data');
            
            // Check if data is valid
            if (!data) {
                console.error('No data received from server');
                showMessage('Error', 'No data received from server. Check the console for details.');
                return;
            }
            
            if (data.success) {
                console.log('Success response received');
                // Verify all required fields are present
                const requiredFields = ['sql', 'intent', 'deployment_script', 'validation'];
                const missingFields = requiredFields.filter(field => !data[field]);
                
                if (missingFields.length > 0) {
                    console.error('Missing required fields in response:', missingFields);
                    showMessage('Warning', `Response is missing some fields: ${missingFields.join(', ')}. Displaying available data.`);
                }
                
                // Display the results with whatever data we have
                console.log('Displaying results container');
                resultsContainer.style.display = 'block';
                displayResults(data);
            } else {
                console.error('Error response received');
                console.error('Error details:', data.error_details || 'No detailed error information available');
                console.error('Error message:', data.error || 'Unknown error');
                showMessage('Error', data.error || 'An error occurred while processing the prompt.');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error processing prompt:', error);
            console.error('Error stack:', error.stack);
            showMessage('Error', 'An error occurred while processing the prompt. Check the console for details.');
        });
    }
    
    // Display the results
    function displayResults(data) {
        // Make sure the results container is visible
        resultsContainer.style.display = 'block';
        
        // SQL content
        if (data.sql) {
            sqlContent.textContent = data.sql;
            console.log('SQL content set:', data.sql);
        } else {
            sqlContent.textContent = 'No SQL query generated.';
            console.warn('No SQL data available');
        }
        
        // Intent content
        if (data.intent) {
            intentContent.textContent = JSON.stringify(data.intent, null, 2);
            console.log('Intent content set');
        } else {
            intentContent.textContent = 'No intent data available.';
            console.warn('No intent data available');
        }
        
        // Deployment script content
        if (data.deployment_script) {
            deploymentContent.textContent = data.deployment_script;
            console.log('Deployment script content set');
        } else {
            deploymentContent.textContent = 'No deployment script generated.';
            console.warn('No deployment script data available');
        }
        
        // Validation content
        if (data.validation) {
            displayValidation(data.validation);
            console.log('Validation content displayed');
        } else {
            validationContent.innerHTML = '<div class="alert alert-warning">No validation data available.</div>';
            console.warn('No validation data available');
        }
        
        // Apply syntax highlighting
        try {
            // Try to use the global hljs instance
            if (typeof window.hljs !== 'undefined') {
                console.log('Applying syntax highlighting...');
                window.hljs.highlightElement(sqlContent);
                window.hljs.highlightElement(intentContent);
                window.hljs.highlightElement(deploymentContent);
                console.log('Syntax highlighting applied successfully');
            } else {
                console.warn('highlight.js not available, skipping syntax highlighting');
            }
        } catch (e) {
            console.error('Error applying syntax highlighting:', e);
            // Continue without syntax highlighting
        }
        
        // Show the results container
        resultsContainer.style.display = 'block';
        
        // Hide execution results
        executionResults.style.display = 'none';
        
        // Highlight the code
        hljs.highlightAll();
    }
    
    // Display validation results
    function displayValidation(validation) {
        validationContent.innerHTML = '';
        
        if (!validation) {
            validationContent.innerHTML = '<div class="alert alert-info">No validation results available.</div>';
            return;
        }
        
        const valid = validation.valid;
        const errors = validation.errors || [];
        const warnings = validation.warnings || [];
        const suggestions = validation.suggestions || [];
        
        if (valid) {
            validationContent.innerHTML += '<div class="alert alert-success">SQL is valid.</div>';
        } else {
            validationContent.innerHTML += '<div class="alert alert-danger">SQL is not valid.</div>';
        }
        
        if (errors.length > 0) {
            validationContent.innerHTML += '<h6 class="mt-3">Errors:</h6>';
            errors.forEach(error => {
                validationContent.innerHTML += `<div class="validation-item validation-error">${error}</div>`;
            });
        }
        
        if (warnings.length > 0) {
            validationContent.innerHTML += '<h6 class="mt-3">Warnings:</h6>';
            warnings.forEach(warning => {
                validationContent.innerHTML += `<div class="validation-item validation-warning">${warning}</div>`;
            });
        }
        
        if (suggestions.length > 0) {
            validationContent.innerHTML += '<h6 class="mt-3">Suggestions:</h6>';
            suggestions.forEach(suggestion => {
                validationContent.innerHTML += `<div class="validation-item validation-suggestion">${suggestion}</div>`;
            });
        }
    }
    
    // Execute SQL
    function executeSql() {
        const sql = sqlContent.textContent;
        if (!sql) {
            showMessage('Error', 'No SQL query to execute.');
            return;
        }
        
        showLoading();
        console.log('Executing SQL query:', sql);
        
        fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: sql })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            console.log('Query execution response:', data);
            
            if (data.success) {
                displayExecutionResults(data.result, data.query_type);
            } else {
                // Check if we have detailed error information
                if (data.error_details) {
                    console.error('Detailed error:', data.error_details);
                }
                
                // Display a user-friendly error message
                let errorMessage = data.error || 'An error occurred while executing the query.';
                
                // Make SQL syntax errors more user-friendly
                if (errorMessage.includes('syntax error')) {
                    errorMessage = 'SQL Syntax Error: ' + errorMessage.split('\n')[0];
                }
                
                showMessage('Error', errorMessage);
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('Error', 'An error occurred while executing the query.');
            console.error('Error:', error);
        });
    }
    
    // Display execution results
    function displayExecutionResults(result, queryType) {
        executionContent.innerHTML = '';
        console.log('Displaying execution results:', result, 'Query type:', queryType);
        
        // Create a header based on query type
        const header = document.createElement('div');
        header.className = 'mb-3';
        
        if (queryType) {
            const badge = document.createElement('span');
            badge.className = 'badge';
            
            // Set badge color based on query type
            switch(queryType) {
                case 'SELECT':
                    badge.className += ' bg-primary';
                    break;
                case 'INSERT':
                    badge.className += ' bg-success';
                    break;
                case 'UPDATE':
                    badge.className += ' bg-warning';
                    break;
                case 'DELETE':
                    badge.className += ' bg-danger';
                    break;
                case 'CREATE_TABLE':
                    badge.className += ' bg-info';
                    break;
                case 'ALTER_TABLE':
                    badge.className += ' bg-secondary';
                    break;
                case 'DROP':
                    badge.className += ' bg-danger';
                    break;
                default:
                    badge.className += ' bg-secondary';
            }
            
            badge.textContent = queryType.replace('_', ' ');
            header.appendChild(badge);
        }
        
        executionContent.appendChild(header);
        
        if (typeof result === 'string') {
            // Check if the message indicates a warning condition (like table already exists)
            if (result.includes('already exists')) {
                const alert = document.createElement('div');
                alert.className = 'alert alert-warning';
                alert.innerHTML = result;
                executionContent.appendChild(alert);
            } 
            // Check if it's a success message
            else if (result.includes('successfully')) {
                const alert = document.createElement('div');
                alert.className = 'alert alert-success';
                alert.innerHTML = result;
                executionContent.appendChild(alert);
            }
            // Default to info for other messages
            else {
                const alert = document.createElement('div');
                alert.className = 'alert alert-info';
                alert.innerHTML = result;
                executionContent.appendChild(alert);
            }
        } else if (Array.isArray(result)) {
            // Display table
            if (result.length === 0) {
                const alert = document.createElement('div');
                alert.className = 'alert alert-info';
                alert.innerHTML = 'Query executed successfully. No results returned.';
                executionContent.appendChild(alert);
            } else {
                // Add a success message before the table
                const successAlert = document.createElement('div');
                successAlert.className = 'alert alert-success mb-3';
                successAlert.textContent = `Query executed successfully. ${result.length} row(s) returned.`;
                executionContent.appendChild(successAlert);
                
                const table = document.createElement('table');
                table.className = 'table table-striped table-bordered result-table';
                
                // Create table header
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                Object.keys(result[0]).forEach(key => {
                    const th = document.createElement('th');
                    th.textContent = key;
                    headerRow.appendChild(th);
                });
                
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Create table body
                const tbody = document.createElement('tbody');
                
                result.forEach(row => {
                    const tr = document.createElement('tr');
                    
                    Object.values(row).forEach(value => {
                        const td = document.createElement('td');
                        
                        // Handle different value types
                        if (value === null) {
                            td.innerHTML = '<em class="text-muted">NULL</em>';
                        } else if (typeof value === 'object') {
                            // For JSON or other complex types
                            td.innerHTML = `<pre class="mb-0">${JSON.stringify(value, null, 2)}</pre>`;
                        } else {
                            td.textContent = value;
                        }
                        
                        tr.appendChild(td);
                    });
                    
                    tbody.appendChild(tr);
                });
                
                table.appendChild(tbody);
                
                // Add table to execution content
                const tableResponsive = document.createElement('div');
                tableResponsive.className = 'table-responsive';
                tableResponsive.appendChild(table);
                
                executionContent.appendChild(tableResponsive);
                
                // Add export buttons if there are results
                if (result.length > 0) {
                    const exportDiv = document.createElement('div');
                    exportDiv.className = 'mt-3';
                    
                    const exportCSVBtn = document.createElement('button');
                    exportCSVBtn.className = 'btn btn-sm btn-outline-secondary me-2';
                    exportCSVBtn.innerHTML = '<i class="bi bi-file-earmark-spreadsheet"></i> Export CSV';
                    exportCSVBtn.onclick = () => exportTableToCSV(result);
                    
                    exportDiv.appendChild(exportCSVBtn);
                    executionContent.appendChild(exportDiv);
                }
            }
        } else {
            const alert = document.createElement('div');
            alert.className = 'alert alert-info';
            alert.innerHTML = 'Query executed successfully.';
            executionContent.appendChild(alert);
        }
        
        // Show execution results
        executionResults.style.display = 'block';
    }
    
    // Export table data to CSV
    function exportTableToCSV(data) {
        if (!data || data.length === 0) return;
        
        // Get headers
        const headers = Object.keys(data[0]);
        
        // Create CSV content
        let csvContent = headers.join(',') + '\n';
        
        // Add rows
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header];
                // Handle null values and escape commas
                if (value === null) return '';
                if (typeof value === 'string' && value.includes(',')) {
                    return `"${value}"`;
                }
                return value;
            });
            csvContent += values.join(',') + '\n';
        });
        
        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', 'sql_results.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Test database connection
    function testConnection() {
        showLoading();
        
        fetch('/api/test-connection')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                showMessage('Connection Test', data.message);
            } else {
                showMessage('Connection Test Failed', data.message || 'Failed to connect to the database.');
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('Error', 'An error occurred while testing the connection.');
            console.error('Error:', error);
        });
    }
    
    // View database schema
    function viewSchema() {
        showLoading();
        
        fetch('/api/schema')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                displaySchema(data.schema);
            } else {
                showMessage('Error', data.error || 'An error occurred while retrieving the schema.');
            }
        })
        .catch(error => {
            hideLoading();
            showMessage('Error', 'An error occurred while retrieving the schema.');
            console.error('Error:', error);
        });
    }
    
    // Display database schema
    function displaySchema(schema) {
        schemaContent.innerHTML = '';
        
        if (!schema || (!schema.tables.length && !schema.views.length && !schema.functions.length)) {
            schemaContent.innerHTML = '<div class="alert alert-info">No schema information available.</div>';
            schemaContainer.style.display = 'block';
            return;
        }
        
        // Display tables
        if (schema.tables.length > 0) {
            schemaContent.innerHTML += '<h5 class="mt-3">Tables</h5>';
            
            schema.tables.forEach(table => {
                const tableDiv = document.createElement('div');
                tableDiv.className = 'schema-table';
                
                const tableNameDiv = document.createElement('div');
                tableNameDiv.className = 'schema-table-name';
                tableNameDiv.textContent = `${table.schema}.${table.name}`;
                tableDiv.appendChild(tableNameDiv);
                
                const tableResponsive = document.createElement('div');
                tableResponsive.className = 'table-responsive';
                
                const tableEl = document.createElement('table');
                tableEl.className = 'table table-sm';
                
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                ['Column', 'Type', 'Nullable', 'Default'].forEach(header => {
                    const th = document.createElement('th');
                    th.textContent = header;
                    headerRow.appendChild(th);
                });
                
                thead.appendChild(headerRow);
                tableEl.appendChild(thead);
                
                const tbody = document.createElement('tbody');
                
                table.columns.forEach(column => {
                    const tr = document.createElement('tr');
                    
                    const tdName = document.createElement('td');
                    tdName.textContent = column.column_name;
                    tr.appendChild(tdName);
                    
                    const tdType = document.createElement('td');
                    tdType.textContent = column.data_type;
                    tr.appendChild(tdType);
                    
                    const tdNullable = document.createElement('td');
                    tdNullable.textContent = column.is_nullable;
                    tr.appendChild(tdNullable);
                    
                    const tdDefault = document.createElement('td');
                    tdDefault.textContent = column.column_default || 'NULL';
                    tr.appendChild(tdDefault);
                    
                    tbody.appendChild(tr);
                });
                
                tableEl.appendChild(tbody);
                tableResponsive.appendChild(tableEl);
                tableDiv.appendChild(tableResponsive);
                
                schemaContent.appendChild(tableDiv);
            });
        }
        
        // Display views
        if (schema.views.length > 0) {
            schemaContent.innerHTML += '<h5 class="mt-4">Views</h5>';
            
            const viewList = document.createElement('ul');
            viewList.className = 'list-group';
            
            schema.views.forEach(view => {
                const viewItem = document.createElement('li');
                viewItem.className = 'list-group-item';
                viewItem.textContent = `${view.view_schema}.${view.view_name}`;
                viewList.appendChild(viewItem);
            });
            
            schemaContent.appendChild(viewList);
        }
        
        // Display functions
        if (schema.functions.length > 0) {
            schemaContent.innerHTML += '<h5 class="mt-4">Functions</h5>';
            
            const functionList = document.createElement('ul');
            functionList.className = 'list-group';
            
            schema.functions.forEach(func => {
                const functionItem = document.createElement('li');
                functionItem.className = 'list-group-item';
                functionItem.textContent = `${func.function_schema}.${func.function_name}`;
                functionList.appendChild(functionItem);
            });
            
            schemaContent.appendChild(functionList);
        }
        
        // Show schema container
        schemaContainer.style.display = 'block';
    }
    
    // Copy to clipboard
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showMessage('Success', 'Copied to clipboard!');
            })
            .catch(err => {
                console.error('Error copying to clipboard:', err);
                showMessage('Error', 'Failed to copy to clipboard.');
            });
    }
    
    // Show message modal
    function showMessage(title, message) {
        const modal = new bootstrap.Modal(document.getElementById('messageModal'));
        document.getElementById('messageModalTitle').textContent = title;
        document.getElementById('messageModalBody').textContent = message;
        modal.show();
    }
    
    // Show loading overlay
    function showLoading() {
        let loadingOverlay = document.querySelector('.loading-overlay');
        
        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            
            const spinner = document.createElement('div');
            spinner.className = 'spinner-border text-light loading-spinner';
            spinner.setAttribute('role', 'status');
            
            const span = document.createElement('span');
            span.className = 'visually-hidden';
            span.textContent = 'Loading...';
            
            spinner.appendChild(span);
            loadingOverlay.appendChild(spinner);
            document.body.appendChild(loadingOverlay);
        }
        
        loadingOverlay.style.display = 'flex';
    }
    
    // Hide loading overlay
    function hideLoading() {
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }
    
    // Database Browser Variables
    let currentTable = null;
    let currentSchema = 'public';
    let currentOffset = 0;
    let totalRows = 0;
    
    // Open Database Browser
    function openDatabaseBrowser() {
        try {
            console.log('Opening database browser');
            
            // Hide other containers
            if (resultsContainer) resultsContainer.style.display = 'none';
            if (executionResults) executionResults.style.display = 'none';
            if (schemaContainer) schemaContainer.style.display = 'none';
            
            // Show database browser container
            if (dbBrowserContainer) {
                dbBrowserContainer.style.display = 'block';
                console.log('Database browser container displayed');
            } else {
                console.error('Database browser container not found');
                showMessage('Error', 'Database browser container not found. Please check the console for more details.');
                return;
            }
            
            // Load tables
            loadTables();
        } catch (error) {
            console.error('Error opening database browser:', error);
            showMessage('Error', 'Failed to open database browser. Please check the console for more details.');
        }
    }
    
    // Load Tables
    function loadTables() {
        showLoading();
        
        fetch('/api/browser/tables')
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.success) {
                    displayTables(data.tables);
                } else {
                    showMessage('Error', data.error || 'Failed to load tables');
                }
            })
            .catch(error => {
                hideLoading();
                showMessage('Error', 'Failed to load tables');
                console.error('Error loading tables:', error);
            });
    }
    
    // Display Tables
    function displayTables(tables) {
        tablesList.innerHTML = '';
        
        if (tables.length === 0) {
            tablesList.innerHTML = '<div class="text-center p-3 text-muted">No tables found</div>';
            return;
        }
        
        // Group tables by schema
        const tablesBySchema = {};
        tables.forEach(table => {
            const schema = table.table_schema;
            if (!tablesBySchema[schema]) {
                tablesBySchema[schema] = [];
            }
            tablesBySchema[schema].push(table);
        });
        
        // Create list items for each table, grouped by schema
        Object.keys(tablesBySchema).sort().forEach(schema => {
            // Add schema header
            const schemaHeader = document.createElement('div');
            schemaHeader.className = 'list-group-item list-group-item-secondary';
            schemaHeader.textContent = schema;
            tablesList.appendChild(schemaHeader);
            
            // Add tables in this schema
            tablesBySchema[schema].sort((a, b) => a.table_name.localeCompare(b.table_name)).forEach(table => {
                const listItem = document.createElement('a');
                listItem.href = '#';
                listItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
                listItem.dataset.table = table.table_name;
                listItem.dataset.schema = table.table_schema;
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = table.table_name;
                listItem.appendChild(nameSpan);
                
                const badge = document.createElement('span');
                badge.className = 'badge bg-secondary rounded-pill';
                badge.textContent = table.column_count;
                listItem.appendChild(badge);
                
                listItem.addEventListener('click', function(e) {
                    e.preventDefault();
                    selectTable(table.table_name, table.table_schema);
                });
                
                tablesList.appendChild(listItem);
            });
        });
    }
    
    // Select Table
    function selectTable(tableName, schemaName) {
        // Update current table and schema
        currentTable = tableName;
        currentSchema = schemaName;
        currentOffset = 0;
        
        // Update selected table name
        selectedTableName.textContent = `${schemaName}.${tableName}`;
        
        // Enable buttons
        tableStructureBtn.disabled = false;
        tableDataBtn.disabled = false;
        
        // Highlight selected table
        const tableItems = tablesList.querySelectorAll('.list-group-item-action');
        tableItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.table === tableName && item.dataset.schema === schemaName) {
                item.classList.add('active');
            }
        });
        
        // Show table structure by default
        showTableStructure();
    }
    
    // Show Table Structure
    function showTableStructure() {
        if (!currentTable) return;
        
        // Update button states
        tableStructureBtn.classList.add('active');
        tableDataBtn.classList.remove('active');
        
        // Show structure container, hide others
        tableStructureContainer.style.display = 'block';
        tableDataContainer.style.display = 'none';
        tableInitialMessage.style.display = 'none';
        
        // Load table structure
        loadTableStructure(currentTable, currentSchema);
    }
    
    // Load Table Structure
    function loadTableStructure(tableName, schemaName) {
        showLoading();
        
        fetch(`/api/browser/table/structure?table=${encodeURIComponent(tableName)}&schema=${encodeURIComponent(schemaName)}`)
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.success) {
                    displayTableStructure(data.structure);
                } else {
                    showMessage('Error', data.error || 'Failed to load table structure');
                }
            })
            .catch(error => {
                hideLoading();
                showMessage('Error', 'Failed to load table structure');
                console.error('Error loading table structure:', error);
            });
    }
    
    // Display Table Structure
    function displayTableStructure(structure) {
        tableStructureBody.innerHTML = '';
        
        if (structure.length === 0) {
            tableStructureBody.innerHTML = '<tr><td colspan="5" class="text-center">No columns found</td></tr>';
            return;
        }
        
        structure.forEach(column => {
            const row = document.createElement('tr');
            
            // Column name
            const nameCell = document.createElement('td');
            nameCell.textContent = column.column_name;
            if (column.is_primary_key) {
                nameCell.innerHTML += ' <span class="badge bg-primary">PK</span>';
            }
            row.appendChild(nameCell);
            
            // Data type
            const typeCell = document.createElement('td');
            let typeText = column.data_type;
            if (column.character_maximum_length) {
                typeText += `(${column.character_maximum_length})`;
            } else if (column.numeric_precision && column.numeric_scale) {
                typeText += `(${column.numeric_precision},${column.numeric_scale})`;
            }
            typeCell.textContent = typeText;
            row.appendChild(typeCell);
            
            // Nullable
            const nullableCell = document.createElement('td');
            nullableCell.textContent = column.is_nullable === 'YES' ? 'Yes' : 'No';
            row.appendChild(nullableCell);
            
            // Default
            const defaultCell = document.createElement('td');
            defaultCell.textContent = column.column_default || '';
            row.appendChild(defaultCell);
            
            // Primary key
            const pkCell = document.createElement('td');
            pkCell.textContent = column.is_primary_key ? 'Yes' : 'No';
            row.appendChild(pkCell);
            
            tableStructureBody.appendChild(row);
        });
    }
    
    // Show Table Data
    function showTableData() {
        if (!currentTable) return;
        
        // Update button states
        tableStructureBtn.classList.remove('active');
        tableDataBtn.classList.add('active');
        
        // Show data container, hide others
        tableStructureContainer.style.display = 'none';
        tableDataContainer.style.display = 'block';
        tableInitialMessage.style.display = 'none';
        
        // Load table data
        loadTableData(currentTable, currentSchema, 0);
    }
    
    // Load Table Data
    function loadTableData(tableName, schemaName, offset) {
        showLoading();
        
        const limit = tableDataLimit.value;
        currentOffset = offset;
        
        fetch(`/api/browser/table/data?table=${encodeURIComponent(tableName)}&schema=${encodeURIComponent(schemaName)}&limit=${limit}&offset=${offset}`)
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.success) {
                    totalRows = data.total_count;
                    displayTableData(data.data, data.total_count, parseInt(data.limit), parseInt(data.offset));
                } else {
                    showMessage('Error', data.error || 'Failed to load table data');
                }
            })
            .catch(error => {
                hideLoading();
                showMessage('Error', 'Failed to load table data');
                console.error('Error loading table data:', error);
            });
    }
    
    // Display Table Data
    function displayTableData(data, totalCount, limit, offset) {
        tableDataHeader.innerHTML = '';
        tableDataBody.innerHTML = '';
        
        if (data.length === 0) {
            tableDataHeader.innerHTML = '<tr><th>No data</th></tr>';
            tableDataBody.innerHTML = '<tr><td class="text-center">No data found</td></tr>';
            tableDataPagination.textContent = 'No data';
            tableDataPrev.disabled = true;
            tableDataNext.disabled = true;
            return;
        }
        
        // Create header row
        const headerRow = document.createElement('tr');
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key;
            headerRow.appendChild(th);
        });
        tableDataHeader.appendChild(headerRow);
        
        // Create data rows
        data.forEach(row => {
            const tr = document.createElement('tr');
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                td.textContent = value !== null ? value : 'NULL';
                if (value === null) {
                    td.className = 'text-muted';
                }
                tr.appendChild(td);
            });
            tableDataBody.appendChild(tr);
        });
        
        // Update pagination
        const start = offset + 1;
        const end = Math.min(offset + data.length, totalCount);
        tableDataPagination.textContent = `Showing ${start} to ${end} of ${totalCount} rows`;
        
        // Update pagination buttons
        tableDataPrev.disabled = offset === 0;
        tableDataNext.disabled = end >= totalCount;
    }
    
    // Load Previous Table Data
    function loadPreviousTableData() {
        if (currentOffset === 0) return;
        
        const limit = parseInt(tableDataLimit.value);
        const newOffset = Math.max(0, currentOffset - limit);
        loadTableData(currentTable, currentSchema, newOffset);
    }
    
    // Load Next Table Data
    function loadNextTableData() {
        const limit = parseInt(tableDataLimit.value);
        const newOffset = currentOffset + limit;
        
        if (newOffset >= totalRows) return;
        
        loadTableData(currentTable, currentSchema, newOffset);
    }
});
