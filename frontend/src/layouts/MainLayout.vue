<template>
  <q-layout view="lHh Lpr lFf">
    <!-- Header: Like a soft cloud or light passing through leaves -->
    <q-header class="bg-transparent text-primary q-py-md q-px-xl" style="backdrop-filter: blur(5px);">
      <q-toolbar>
        <q-toolbar-title class="text-weight-light" style="font-family: serif; letter-spacing: 1px;">
          Network<span class="text-secondary">Pulse</span>
        </q-toolbar-title>

        <q-btn flat rounded dense label="Collection" to="/admin/hars" class="q-mr-sm text-capitalize q-px-lg" style="min-width: 140px" />
        <q-btn flat rounded dense label="Root Access" to="/admin" class="text-capitalize q-px-lg" style="min-width: 140px" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
</script>
