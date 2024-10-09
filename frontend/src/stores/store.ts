import { defineStore } from 'pinia';

export const useDocumentStore = defineStore({
  id: 'document',
  state: () => ({
    documentData: null,
  }),
  actions: {
    setDocumentData(data: any) {
      this.documentData = data;
    },
  },
});
