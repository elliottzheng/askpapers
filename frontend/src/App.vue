<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <nav>
      <RouterLink to="/library">文献库</RouterLink>
      <RouterLink to="/chat">聊天</RouterLink>
    </nav>
  </header>
  <main>
    <RouterView/>
  </main>
</template>

<style scoped>
header {
  line-height: 1.5;
  width: 100%;
  top: 0;
  left: 0;
  background-color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 100;
  position: sticky;
}

nav {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 8px;
  font-size: 16px;
}

nav a {
  margin: 0 1rem;
  padding: 0.5rem 1rem;
  text-decoration: none;
  color: #666;
  border-radius: 4px;
  transition: all 0.3s ease;
}

nav a:hover {
  background-color: #f0f0f0;
}

nav a.router-link-exact-active {
  color: #42b983;
  font-weight: bold;
}

#app {
  width: 100%;
}

/* 为了避免内容被固定导航栏遮挡 */
main {
  /* margin-top: 60px; */
  width: 100%;
  /* 防止出现水平滚动条 */
  box-sizing: border-box;
}

</style>