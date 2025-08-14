Top Accounts Widget

- The placeholder items (....) and (----) should be replaced with their final components
- One will be a visualization of some facet of the account (eg historical balance displayed as a minimalistic line)

Daily Net Chart

- Need to exclude 'Internal' transactions such as self-transfers. This logic may exist already but needs to be propogated throughout full dashboard
- Modal: Clicking on a transaction in the modal will take you to the UpdateTransactionTable.vue on the Transactions page (filtered on the same filter that the Modal was)
  - This would allow for editing incorrect transactions or modifying details
  - Should this action happen on click on any transaction? Or should I integrate a 'view' or 'edit details' button?

Category Breakdown Chart

- Required fixes: Chart should display top 5 if 'Grouped' is toggled. Display = Top 4 + 'Other'
- The dropdown menu should exit on-click if cick anywhere outside the menu + if click the menu name to collapse

Spending Insights

- Include average spending per day
  - This could be a moving average
  - Could optionally be displayed on the Daily Net chart
  - Would be toggleable at first to determine whether it should be implemented
  -
