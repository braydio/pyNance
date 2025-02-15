<template>
    <div>
        <h1>Accounts</h1>
        <button @click="refreshAccounts">Refresh Accounts</button>
        <div v-if="loading">Loading...</div>
        <div v-else-if="error">{{ error }}</div>
        <table v-if="accounts.length">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Institution</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="account in accounts" :key="account.id">
                    <td>{{ account.name }}</td>
                    <td>{{ account.type }} ({{ account.subtype }})</td>
                    <td>{{ account.status }}</td>
                    <td>{{ account.institution.name }}</td>
                </tr>
            </tbody>
        </table>
        <div v-else>No accounts available.</div>
    </div>
</template>

<script>
import { refreshAccounts, getAccounts } from "../api/teller";

export default {
    name: "AccountsTable",
    data() {
        return {
            accounts: [], // Initialize as an empty array
            loading: false,
            error: null,
        };
    },
    methods: {
        async fetchAccounts() {
            this.loading = true;
            this.error = null;
            try {
                const response = await getAccounts();
                this.accounts = response.data || []; // Safeguard against undefined
            } catch (error) {
                this.error = "Failed to fetch accounts.";
                console.error(error);
            } finally {
                this.loading = false;
            }
        },
        async refreshAccounts() {
            this.loading = true;
            this.error = null;
            try {
                await refreshAccounts();
                await this.fetchAccounts();
            } catch (error) {
                this.error = "Failed to refresh accounts.";
                console.error(error);
            } finally {
                this.loading = false;
            }
        },
    },
    mounted() {
        this.fetchAccounts();
    },
};

</script>

<style scoped>
table {
    width: 100%;
    border-collapse: collapse;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
}
th {
    background-color: #f4f4f4;
}
</style>
