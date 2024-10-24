import React, { useEffect, useState } from 'react';
import axios from 'axios';
import CustomNavbar from "./Header";
import { Form, Label, Input, FormGroup, Button } from "reactstrap";

function Customer() {
  const [question, setQuestion] = useState('');  // To store user input question
  const [output, setOutput] = useState('');      // To store the API response (SQL query and results)



  // Handle fetching the answer for the user's question
  const handleGetAnswer = async (e) => {
    e.preventDefault();

    if (!question) {
      alert('Please enter a question!');
      return;
    }

    setOutput(''); 

    try {
      const response = await axios.post('http://127.0.0.1:8000/project/generate-related-query/', { text: question });
      
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
        {/* Question Input Section */}
        <h1>Get all Info </h1> 
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

export default Customer;
