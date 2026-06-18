
// --- GLOBAL APPLICATION CONFIGURATIONS ---
const API_BASE_URL = "http://localhost:8000";

/**
 * Global helper function to handle API error responses cleanly.
 * Converts backend validation or business-logic errors into clear feedback.
 */
async function handleResponseError(response) {
    try {
        const errorData = await response.json();
        if (errorData && errorData.detail) {
            return errorData.detail;
        }
    } catch (e) {
        // Fallback if response isn't JSON string streams
    }
    return `Server communication failed (Status: ${response.status})`;
}