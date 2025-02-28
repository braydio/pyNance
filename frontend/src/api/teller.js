import axios from "axios";

const API_URL = "/api/teller_transactions";

export const refreshAccounts = async () => {
    try {
        const response = await axios.post(`api/teller/refresh_accounts`);
        return response.data;
    } catch (error) {
        console.error("Error refreshing accounts:", error.response || error);
        throw error;
    }
};

export const getAccounts = async () => {
    try {
        const response = await axios.get(`api/teller/get_accounts`);
        return response.data;
    } catch (error) {
        console.error("Error fetching accounts:", error.response || error);
        throw error;
    }
};
