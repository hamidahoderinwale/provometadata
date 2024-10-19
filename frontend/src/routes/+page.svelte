
<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  let files = [];
  let query = '';
  let message = '';
  let isConnected = false;
  let isLoading = false;

  // Check server connection on mount
  onMount(async () => {
    try {
      await axios.get('http://localhost:8000/health');
      isConnected = true;
      message = 'Connected to server';
    } catch (error) {
      isConnected = false;
      message = 'Error connecting to server';
      console.error('Error connecting to server:', error);
    }
  });

  // Upload PDF files
  const uploadFiles = async () => {
    if (files.length === 0) {
      message = 'Please select files to upload';
      return;
    }

    // Filter for PDF files
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');

    // Ensure at least 5 PDF files are selected
    if (pdfFiles.length < 5) {
      message = 'Please select at least 5 PDF files.';
      return;
    }

    isLoading = true;
    message = 'Uploading files...';

    const formData = new FormData();
    for (const file of pdfFiles) {
      formData.append('files', file);
    }

    try {
      const response = await axios.post('http://localhost:8000/add_documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      message = 'Files uploaded and added to collection successfully';
      console.log('Files uploaded successfully:', response.data);
    } catch (error) {
      message = 'Error uploading files: ' + (error.response?.data?.detail || error.message);
      console.error('Error uploading files:', error);
    } finally {
      isLoading = false;
    }
  };

  // Submit query to the server
  const submitQuery = async () => {
    if (!query) {
      message = 'Please enter a query';
      return;
    }

    isLoading = true;
    message = 'Processing query...';
    console.log('Submitting query:', query);

    try {
      const response = await axios.post('http://localhost:8000/process', 
        { text: query },
        { 
          responseType: 'blob',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'query_results.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

      message = 'Query processed successfully. CSV downloaded.';
    } catch (error) {
      if (error.response) {
        message = `Error processing query: ${error.response.status} ${error.response.statusText}`;
        console.error("Error data:", error.response.data);
      } else if (error.request) {
        message = 'Error processing query: No response received from server';
        console.error("Error request:", error.request);
      } else {
        message = 'Error processing query: ' + error.message;
        console.error('Error message:', error.message);
      }
    } finally {
      isLoading = false;
    }
  };
</script>

<main>
  <h1>Provo</h1>
  <p>Convert any set of PDFs into customized structured data files</p>

  <div class="status {isConnected ? 'connected' : 'disconnected'}">
    Server status: {isConnected ? 'Connected' : 'Disconnected'}
  </div>

  <div class="upload-section">
    <input type="file" accept="application/pdf" multiple bind:files={files} />
    <button on:click={uploadFiles} disabled={isLoading || !isConnected}>Upload PDFs</button>
  </div>

  <div class="query-section">
    <input type="text" bind:value={query} placeholder="Enter your query here..." disabled={isLoading || !isConnected} />
    <button on:click={submitQuery} disabled={isLoading || !isConnected}>Submit Query</button>
  </div>

  {#if isLoading}
    <div class="loading">Processing...</div>
  {/if}

  {#if message}
    <p class="message">{message}</p>
  {/if}
</main>

<style>
  /* Add your styles here */
  .status {
    margin: 10px 0;
  }
  .connected {
    color: green;
  }
  .disconnected {
    color: red;
  }
  .upload-section,
  .query-section {
    margin: 20px 0;
  }
  .loading {
    font-weight: bold;
  }
  .message {
    color: blue;
  }
</style>
