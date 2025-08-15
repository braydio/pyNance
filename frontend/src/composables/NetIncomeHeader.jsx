import React from 'react';

const NetIncomeHeader = () => {
  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: '10px 20px',
    backgroundColor: '#f0f0f0',
    borderBottom: '1px solid #ddd',
    fontSize: '1.25em',
    fontWeight: 'bold',
    color: '#333',
  };

  const titleStyle = {
    fontSize: '1.5em',
    marginRight: '20px',
  };

  const itemStyle = {
    flex: 1,
    textAlign: 'center',
    fontWeight: 'bold',
  };

  return (
    <div style={headerStyle}>
      <div style={{ ...itemStyle, color: 'green' }}>Income</div>
      <div style={{ ...itemStyle, color: 'red' }}>Expenses</div>
      <div style={{ ...itemStyle, color: 'black' }}>Net Total</div>
    </div>
  );
};

export default NetIncomeHeader;
