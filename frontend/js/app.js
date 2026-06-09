// --- GLOBAL APPLICATION CONFIGURATIONS ---

// The local address where your Dockerized FastAPI server runs
const API_BASE_URL = "http://localhost:8000";

/**
 * Global helper function to handle API error responses cleanly.
 * This converts backend errors (like out of stock) into friendly alert messages for the shopkeeper.
 */
async function handleResponseError(response) {
    try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
            return errorData.detail;
        }
    } catch (e) {
        // Fallback if response isn't JSON
    }
    return `Server communication failed (Status: ${response.status})`;
}