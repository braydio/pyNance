T<template>
    <header>
      <div>
        <h1>Brayden.com</h1>
        <h3>Finance</h3>
      </div>
      <nav class="menu">
        <button @click="navigate('/')">Dashboard</button>
        <button @click="navigate('/teller-dot')">Teller.IO</button>
        <button @click="navigate('/accounts')">Accounts</button>
        <button @click="navigate('/transactions')">Transactions</button>
        <button @click="navigate('/settings')">Settings</button>
      </nav>
    </header>
  </template>
  
  <script>
  export default {
    methods: {
      navigate(path) {
        this.$router.push(path);
      },
    },
  };
  </script>
  
  <style scoped>
  header {
    background-color: #4caf50;
    padding: 20px;
    color: white;
    text-align: center;
  }
  
  nav button {
    margin: 5px;
    padding: 10px;
    cursor: pointer;
  }
  </style>
  