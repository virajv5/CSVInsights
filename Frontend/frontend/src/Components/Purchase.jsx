import React, { useEffect, useState } from 'react';
import axios from 'axios';
import CustomNavbar from "./Header";
import { Form, Label, Input, FormGroup, Button } from "reactstrap";

function Sales() {
  const [csvFile, setCsvFile] = useState(null);  // To store the uploaded file
  const [question, setQuestion] = useState('');  // To store user input question
  const [output, setOutput] = useState('');      // To store the API response (SQL query and results)

  // Handle CSV file upload
  const handleFileUpload = async (e) => {
    e.preventDefault();
    
    if (!csvFile) {
      alert('Please upload a CSV file!');
      return;
    }

    const formData = new FormData();
    formData.append('csv_file', csvFile);

    try {
      await axios.post('http://127.0.0.1:8000/project/upload-Purchase-csv/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      alert('CSV uploaded successfully!');
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload CSV file.');
    }
  };

  // Handle fetching the answer for the user's question
  const handleGetAnswer = async (e) => {
    e.preventDefault();

    if (!question) {
      alert('Please enter a question!');
      return;
    }

    setOutput(''); 

    try {
      const response = await axios.post('http://127.0.0.1:8000/project/generate-purchase-query/', { text: question });
      
      // Format the result for display
      const result = response.data.results
        ? JSON.stringify(response.data.results, null, 2)
        : response.data.error || 'No results found';

      setOutput(`SQL Query: ${response.data.sql_query}\n\nResults: ${result}`);
    } catch (error) {
      console.error('Error fetching answer:', error);
      setOutput('Error retrieving answer.');
    }
  };

  return (
    <>
      <CustomNavbar />
      <Form style={{ width: "800px", marginTop: "10px", marginLeft: "450px" }}>
        <br />
        {/* CSV File Upload Section */}
        <FormGroup>
          <Label for="csv_file">Upload Your Purchase CSV</Label>
          <Input 
            id="csv_file" 
            name="csv_file" 
            type="file" 
            onChange={(e) => setCsvFile(e.target.files[0])}  // Set the uploaded file
          />
        </FormGroup>
        <Button className="btn btn-success" type="submit" onClick={handleFileUpload}>Submit</Button>
        <br /> <br />

        {/* Question Input Section */}
        <h1>Get Purchase Info</h1> 
        <br /> 
        <FormGroup>
          <Label for="text">Ask a question</Label>
          <Input 
            id="text" 
            type="textarea" 
            value={question} 
            onChange={(e) => setQuestion(e.target.value)}  // Set the user's question
          />
        </FormGroup>
        <Button className="btn btn-primary" type="submit" onClick={handleGetAnswer}>Get Answer</Button>
        <br /><br />

        {/* Output Display Section */}
        <h1>Output</h1> 
        <br />
        <Input 
          id="output" 
          type="textarea" 
          value={output} 
          readOnly  // Make the output textarea read-only
          style={{ height: '300px' }}  // Increase height for better visibility
        /> 

      </Form>
    </>
  );
}

export default Sales;
