<template>
    <div id="upload-return-receipt">
      <h1>Schritt 1: Retourschein/Remission hochladen </h1>
      <input type="file" @change="handleFileUpload" />
  
      <!-- Tabelle zum Anzeigen der Inhalte -->
      <table v-if="documentStore.documentData">
        <thead>
          <tr>
            <th>Titel</th>
            <th>Objektnr</th>
            <th>Folge</th>
            <th>LM</th>
            <th>RM</th>
            <th>MWST.</th>
            <th>EK.Pr.</th>
            <th>VK.Pr.</th>
            <th>Gutschrift RM</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in documentStore.documentData.content" :key="index">
            <td>{{ item.Titel }}</td>
            <td>{{ item.Objektnr }}</td>
            <td>{{ item.Folge }}</td>
            <td>{{ item.LM }}</td>
            <td>{{ item.RM }}</td>
            <td>{{ item.MWST }}</td>
            <td>{{ item['EK.Pr.'] }}</td>
            <td>{{ item['VK.Pr.'] }}</td>
            <td>{{ item.Gutschrift_RM }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script lang="ts">
  import { defineComponent } from 'vue';
  import { useDocumentStore } from '@/stores/store';
  import axios from 'axios';
  
  export default defineComponent({
    name: 'UploadReturnReceipt',
    setup() {
      const documentStore = useDocumentStore();
  
      const handleFileUpload = async (event: Event) => {
        const target = event.target as HTMLInputElement;
        const file = target.files ? target.files[0] : null;
  
        if (file) {
          const formData = new FormData();
          formData.append('file', file);
  
          try {
            // API-Aufruf zum Hochladen der Datei
            const response = await axios.post('http://127.0.0.1:5000/tables/upload_pdf', formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
              },
            });
  
            // Speichere die API-Antwort im Store
            documentStore.setDocumentData(response.data);
          } catch (error) {
            console.error('Fehler beim Hochladen:', error);
          }
        }
      };
  
      return {
        handleFileUpload,
        documentStore,
      };
    },
  });
  </script>
  
  <style scoped>
  #upload-return-receipt {
    background-color: beige;
    color: black;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  th, td {
    border: 1px solid black;
    padding: 8px;
    text-align: left;
  }
  </style>
  