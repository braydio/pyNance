$(document).ready(function () {
    $('#transactions-table').DataTable({
        pageLength: 20, // Show 20 rows per page
        ordering: true, // Enable column sorting
        order: [[0, 'desc']], // Default sort by Date column (descending)
        columnDefs: [
            { type: 'num', targets: 4 } // Enable numeric sorting for Amount column
        ],
        language: {
            search: "Filter transactions:", // Custom search text
            emptyTable: "No transactions to display." // Custom empty table message
        },
        scrollY: "60vh", // Enable vertical scrolling for large datasets
        scrollCollapse: true, // Collapse the table to fit the container
    });
});