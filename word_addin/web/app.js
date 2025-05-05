// FDA Oncology Copilot Word Add-in

// The initialize function is run each time the page is loaded
Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        // Initialize UI
        loadDataSources();
        loadSupportedFormats();
        
        // Set up event handlers
        document.getElementById("dataSource").addEventListener("change", loadMetadataOptions);
        document.getElementById("summarizeBtn").addEventListener("click", summarizeSelectedText);
        document.getElementById("insertBtn").addEventListener("click", insertSummaryIntoDocument);
        document.getElementById("uploadBtn").addEventListener("click", uploadAndProcessFile);
    } else {
        // Not running in Word
        showError("This add-in is designed to work with Microsoft Word.");
    }
});

/**
 * Load supported file formats from the API
 */
async function loadSupportedFormats() {
    try {
        const response = await fetch("http://localhost:8000/api/supported_formats");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const formats = data.formats;
        
        // Display supported formats
        const formatsText = formats.join(", ");
        document.getElementById("supportedFormats").innerHTML = 
            `<p>Supported formats: ${formatsText}</p>`;
    } catch (error) {
        console.error("Error loading supported formats:", error);
        document.getElementById("supportedFormats").innerHTML = 
            `<p>Supported formats: .txt, .pdf, .docx (Error loading complete list)</p>`;
    }
}

/**
 * Load available data sources from the API
 */
async function loadDataSources() {
    try {
        const response = await fetch("http://localhost:8000/api/sources");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const sources = await response.json();
        
        const select = document.getElementById("dataSource");
        select.innerHTML = ""; // Clear existing options
        
        if (sources.length === 0) {
            showError("No data sources found. Please ensure indices are built.");
            return;
        }
        
        sources.forEach(source => {
            const option = document.createElement("option");
            option.value = source.id;
            option.textContent = source.name;
            select.appendChild(option);
        });
        
        // Load metadata options for the first source
        loadMetadataOptions();
    } catch (error) {
        console.error("Error loading data sources:", error);
        showError("Failed to load data sources. Please ensure the backend service is running.");
    }
}

/**
 * Load metadata options for the selected data source
 */
async function loadMetadataOptions() {
    const sourceId = document.getElementById("dataSource").value;
    
    if (!sourceId) {
        return; // No source selected
    }
    
    try {
        const response = await fetch(`http://localhost:8000/api/metadata?source=${encodeURIComponent(sourceId)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const metadata = await response.json();
        
        // Populate disease type dropdown
        populateSelect("diseaseType", metadata.disease_type || []);
        
        // Populate trial phase dropdown
        populateSelect("trialPhase", metadata.phase || []);
        
        // Populate document section dropdown
        populateSelect("documentSection", metadata.section || []);
    } catch (error) {
        console.error("Error loading metadata options:", error);
        showError("Failed to load filter options.");
    }
}

/**
 * Populate a select element with options
 * 
 * @param {string} id - The ID of the select element
 * @param {Array} options - Array of option values
 */
function populateSelect(id, options) {
    const select = document.getElementById(id);
    select.innerHTML = ""; // Clear existing options
    
    // Add "All" option
    const allOption = document.createElement("option");
    allOption.value = "All";
    allOption.textContent = "All";
    select.appendChild(allOption);
    
    // Add other options
    options.forEach(option => {
        if (option !== "All") {
            const optionElement = document.createElement("option");
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        }
    });
}

/**
 * Summarize the selected text in the Word document
 */
async function summarizeSelectedText() {
    // Hide previous results and errors
    document.getElementById("results").classList.add("hidden");
    document.getElementById("error").classList.add("hidden");
    document.getElementById("validation").classList.add("hidden");
    
    // Get selected text from Word
    Office.context.document.getSelectedDataAsync(Office.CoercionType.Text, async (result) => {
        if (result.status === Office.AsyncResultStatus.Succeeded) {
            const text = result.value;
            
            if (text.trim() === "") {
                showError("Please select text to summarize.");
                return;
            }
            
            // Get filters
            const filters = {};
            
            const diseaseType = document.getElementById("diseaseType").value;
            if (diseaseType !== "All") {
                filters.disease_type = diseaseType;
            }
            
            const trialPhase = document.getElementById("trialPhase").value;
            if (trialPhase !== "All") {
                filters.phase = trialPhase;
            }
            
            const documentSection = document.getElementById("documentSection").value;
            if (documentSection !== "All") {
                filters.section = documentSection;
            }
            
            // Show loading indicator
            document.getElementById("loading").classList.remove("hidden");
            
            try {
                // Prepare request body
                const requestBody = {
                    text: text,
                    source: document.getElementById("dataSource").value,
                    filters: {}, // Always include filters as an empty object
                    k: 3
                };
                
                // Add selected filters if there are any
                if (Object.keys(filters).length > 0) {
                    requestBody.filters = filters;
                }
                
                console.log("Sending request with body:", JSON.stringify(requestBody));
                
                // Call API to summarize text
                const response = await fetch("http://localhost:8000/api/summarize", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(requestBody)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Display results
                document.getElementById("summary").textContent = result.summary;
                
                // Display references
                const referencesDiv = document.getElementById("references");
                referencesDiv.innerHTML = "";
                
                result.references.forEach((reference, index) => {
                    const referenceDiv = document.createElement("div");
                    referenceDiv.className = "reference";
                    
                    const heading = document.createElement("h3");
                    heading.textContent = `Reference ${index + 1}`;
                    
                    const content = document.createElement("p");
                    content.textContent = reference;
                    
                    referenceDiv.appendChild(heading);
                    referenceDiv.appendChild(content);
                    
                    // Add metadata if available
                    if (result.metadata && result.metadata[index]) {
                        const metadata = result.metadata[index];
                        const metadataP = document.createElement("p");
                        metadataP.className = "metadata";
                        
                        for (const key in metadata) {
                            if (key !== "chunk_id" && key !== "source") {
                                metadataP.innerHTML += `<strong>${key}:</strong> ${metadata[key]}<br>`;
                            }
                        }
                        
                        referenceDiv.appendChild(metadataP);
                    }
                    
                    referencesDiv.appendChild(referenceDiv);
                });
                
                // Show validation warning if needed
                if (result.validation && !result.validation.is_valid) {
                    const validationDiv = document.getElementById("validation");
                    document.getElementById("validationMessage").textContent = 
                        `Warning: The summary may be missing important oncology terms: ${result.validation.missing_terms.join(", ")}`;
                    validationDiv.classList.remove("hidden");
                }
                
                // Show results section
                document.getElementById("results").classList.remove("hidden");
            } catch (error) {
                console.error("Error summarizing text:", error);
                showError("An error occurred while summarizing the text. Please try again.");
            } finally {
                // Hide loading indicator
                document.getElementById("loading").classList.add("hidden");
            }
        } else {
            showError("Failed to get selected text: " + result.error.message);
        }
    });
}

/**
 * Insert the generated summary into the Word document
 */
function insertSummaryIntoDocument() {
    const summary = document.getElementById("summary").textContent;
    
    if (!summary) {
        showError("No summary to insert.");
        return;
    }
    
    // Insert summary at current selection
    Office.context.document.setSelectedDataAsync(summary, {
        coercionType: Office.CoercionType.Text
    }, (result) => {
        if (result.status === Office.AsyncResultStatus.Succeeded) {
            showMessage("Summary inserted successfully!");
        } else {
            showError("Failed to insert summary: " + result.error.message);
        }
    });
}

/**
 * Show an error message
 * 
 * @param {string} message - The error message to display
 */
function showError(message) {
    const errorDiv = document.getElementById("error");
    document.getElementById("errorMessage").textContent = message;
    errorDiv.classList.remove("hidden");
}

/**
 * Upload and process a file
 */
async function uploadAndProcessFile() {
    // Get the file input element
    const fileInput = document.getElementById("fileUpload");
    
    // Check if a file is selected
    if (!fileInput.files || fileInput.files.length === 0) {
        showError("Please select a file to upload.");
        return;
    }
    
    const file = fileInput.files[0];
    // Use the first available data source (since we're using all sources anyway)
    const sourceId = document.getElementById("dataSource").value;
    
    // Hide previous results and errors
    document.getElementById("results").classList.add("hidden");
    document.getElementById("error").classList.add("hidden");
    document.getElementById("validation").classList.add("hidden");
    
    // Show loading indicator
    document.getElementById("loading").classList.remove("hidden");
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append("file", file);
        formData.append("source", sourceId);
        
        // Upload the file
        const response = await fetch("http://localhost:8000/api/upload", {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error uploading file");
        }
        
        const result = await response.json();
        
        // Insert the extracted text into the document
        Office.context.document.setSelectedDataAsync(result.text, {
            coercionType: Office.CoercionType.Text
        }, (insertResult) => {
            if (insertResult.status === Office.AsyncResultStatus.Succeeded) {
                showMessage(`File "${result.filename}" processed and inserted successfully!`);
            } else {
                showError(`File processed but could not be inserted: ${insertResult.error.message}`);
            }
        });
    } catch (error) {
        console.error("Error uploading file:", error);
        showError(`Error processing file: ${error.message}`);
    } finally {
        // Hide loading indicator
        document.getElementById("loading").classList.add("hidden");
        
        // Clear the file input
        fileInput.value = "";
    }
}

/**
 * Show a success message (could be implemented with a toast or notification)
 * 
 * @param {string} message - The message to display
 */
function showMessage(message) {
    // For now, we'll just use an alert, but this could be improved
    alert(message);
}
