
<h1>Provo</h1>
<p>Convert any set of PDFs into customized structured data files</p>



<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    let file;

const uploadFile = async () => {
  if (!file) return;

  const formData = new FormData();
  formData.append('pdf', file);

  try {
    const response = await axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    console.log('File uploaded successfully:', response.data);
  } catch (error) {
    console.error('Error uploading file:', error);
  }
};
</script>

<input type="file" accept="application/pdf" on:change="{(e) => file = e.target.files[0]}" />
<button on:click="{uploadFile}">Upload PDF</button>



